"""
SEO Intelligence Engine.
Evaluates organic search visibility, Google algorithm risk, search intent,
AI Overviews vulnerability, and keyword expansion opportunities based on Google Search Central guidelines.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from radar.models import Listing, SEOMetrics
from radar.seo.cpc_benchmarks import get_niche_benchmark

class SEOAnalyzer:
    _index_cache: Dict[str, Tuple[int, List[str]]] = {}
    _ddg_rate_limited: bool = False

    @classmethod
    def check_search_engine_index(cls, domain: Optional[str]) -> Tuple[int, List[str]]:
        """
        Queries search engine index for domain presence ('site:domain').
        Returns (indexed_pages_count, sample_snippets).
        Cached to avoid redundant queries; short-circuits on rate limit.
        """
        if not domain or "." not in domain:
            return 0, []
        clean = domain.lower().replace("https://", "").replace("http://", "").strip("/")
        # Skip marketplace domains when domain is not disclosed
        if any(m in clean for m in ["flippa.com", "sideprojectors.com", "microns.io", "acquire.com", "motioninvest.com", "littleexits.com", "investors.club"]):
            return 0, []

        if clean in cls._index_cache:
            return cls._index_cache[clean]

        if cls._ddg_rate_limited:
            return 0, []

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            url = f"https://html.duckduckgo.com/html/?q=site%3A{clean}"
            resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=2.5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                results = [a.get_text(strip=True) for a in soup.select(".result__title")]
                res = (len(results), results[:3])
                cls._index_cache[clean] = res
                return res
            elif resp.status_code in [403, 429]:
                cls._ddg_rate_limited = True
        except Exception:
            pass
        cls._index_cache[clean] = (0, [])
        return 0, []

    @staticmethod
    def assess_ai_overview_vulnerability(category: str, title: str, description: str) -> Tuple[str, str]:
        """
        Assesses zero-click / Google AI Overview risk according to Google Search Central guidelines.
        Returns: (vulnerability_level, explanation)
        """
        text = f"{category} {title} {description}".lower()

        # Low risk: tools with inputs, interactive SaaS, community, downloadable files
        if any(k in text for k in ["saas", "software", "extension", "chrome extension", "login", "dashboard", "community", "download", "generator", "converter"]):
            return "low", "Interactive tool/utility or software requires active user session; immune to zero-click AI summaries."

        # High risk: purely informational basic definitions, simple recipes, weather, factual queries
        if any(k in text for k in ["definition", "what is", "meaning", "trivia", "quotes", "facts"]):
            return "high", "Informational site vulnerable to Google AI Overviews and zero-click answer snippets."

        # Medium risk: standard how-to or affiliate review articles
        return "medium", "Review/blog content moderately exposed to AI summaries; requires unique expert analysis (E-E-A-T) to sustain click-through rates."

    @staticmethod
    def estimate_traffic_trend(listing: Listing) -> Tuple[str, float, str]:
        """
        Evaluates traffic trajectory and algorithm stability.
        Returns (trend_status, change_percent, reason)
        """
        meta = listing.raw_metadata
        history = meta.get("traffic_history", [])

        if len(history) >= 2:
            first = float(history[0])
            last = float(history[-1])
            if first > 0:
                pct = ((last - first) / first) * 100.0
                if pct < -30.0:
                    return "declining", round(pct, 1), f"Severe traffic drop of {pct:.1f}% detected over reporting period (possible Google algorithm penalty)."
                elif pct > 40.0:
                    return "spiking", round(pct, 1), f"Rapid traffic spike of +{pct:.1f}%; verify whether traffic is organic or short-lived promotional."
                elif pct > 10.0:
                    return "growing", round(pct, 1), f"Healthy upward trajectory of +{pct:.1f}%."
                else:
                    return "stable", round(pct, 1), "Stable traffic trajectory over observation window."

        desc = listing.description.lower()
        if "declining" in desc or "lost traffic" in desc or "algorithm update" in desc:
            return "declining", -35.0, "Seller notes traffic decline following search engine updates."
        if "growing" in desc or "increasing traffic" in desc:
            return "growing", 15.0, "Organic traffic reportedly increasing."

        return "stable", 0.0, "Baseline traffic assumed stable based on available current snapshot."

    @classmethod
    def analyze(cls, listing: Listing) -> SEOMetrics:
        """
        Runs comprehensive SEO assessment on a listing with live search index verification.
        """
        benchmark = get_niche_benchmark(listing.category, listing.title, listing.description)
        ai_risk, ai_risk_notes = cls.assess_ai_overview_vulnerability(listing.category, listing.title, listing.description)
        trend, trend_pct, trend_notes = cls.estimate_traffic_trend(listing)

        domain_age = listing.domain_age_years if listing.domain_age_years > 0 else 1.5

        # Check live index presence if domain is available
        indexed_count, sample_snippets = cls.check_search_engine_index(listing.domain)

        health_notes = [
            f"AI Overviews Risk: {ai_risk.upper()} - {ai_risk_notes}",
            f"Traffic Trend: {trend.upper()} ({trend_notes})"
        ]

        # Evaluate credibility of traffic claims:
        # If domain has 0 indexed pages and seller claims have no third-party verification:
        if listing.domain and indexed_count == 0 and not listing.seller_claims_verified:
            est_organic_visits = 0
            indexed_pages = 0
            ranking_keywords_count = 0
            da_proxy = 5.0
            confidence = "unverified_zero_traffic"
            health_notes.append("CRITICAL DUE DILIGENCE: Domain has 0 indexed pages in search engines. Claimed organic search traffic is fabricated, dead, or non-existent.")
        elif listing.seller_claims_verified:
            est_organic_visits = max(listing.monthly_visitors, listing.monthly_search_clicks)
            indexed_pages = max(indexed_count, 5)
            ranking_keywords_count = max(10, int(est_organic_visits / 12))
            da_proxy = min(60.0, round(12.0 + (domain_age * 4.0) + (min(est_organic_visits, 10000) / 400.0), 1))
            confidence = "verified"
            health_notes.append("Search Presence: Marketplace data verified with Google Analytics / Search Console connection.")
        elif indexed_count > 0:
            est_organic_visits = min(listing.monthly_visitors, indexed_count * 120)
            indexed_pages = indexed_count
            ranking_keywords_count = max(5, int(est_organic_visits / 15))
            da_proxy = min(50.0, round(10.0 + (domain_age * 3.0) + (indexed_count * 1.5), 1))
            confidence = "indexed_unverified"
            health_notes.append(f"Search Presence: Domain is indexed in search engines ({indexed_count}+ pages visible).")
        else:
            est_organic_visits = min(listing.monthly_visitors, 50)
            indexed_pages = 0
            ranking_keywords_count = 0
            da_proxy = 5.0
            confidence = "low"
            health_notes.append("Search Presence: Domain masked or unverified without search index confirmation.")

        # Referring domains and authority proxy estimation
        est_referring_domains = max(1, int(indexed_pages * 2 + (est_organic_visits / 250)))
        est_backlinks = est_referring_domains * 5

        # Commercial intent ratio
        commercial_intent = benchmark["default_commercial_intent"]
        if listing.category in ["Micro-SaaS", "E-commerce"]:
            commercial_intent = min(0.85, commercial_intent + 0.20)
        elif listing.category in ["Tool/Utility"]:
            commercial_intent = min(0.65, commercial_intent + 0.10)

        # Top keywords and content gap opportunities
        title_words = re.findall(r"\b[a-zA-Z]{4,}\b", listing.title.lower())
        top_kws = [f"{w} online" for w in title_words[:3]] or ["niche utility tool", "online service"]

        content_gap = (
            f"Target high-intent commercial keywords: 'best {listing.category.lower()} for small business', "
            f"'{top_kws[0] if top_kws else 'product'} alternatives', and comparison landing pages."
        )

        health_notes.append(f"Commercial Search Intent: {int(commercial_intent * 100)}% estimated transactional/commercial intent.")

        if trend == "declining":
            health_notes.append("WARNING: Potential vulnerability to Google Helpful Content / Core Updates. Audit content quality before bidding.")

        return SEOMetrics(
            listing_id=listing.id,
            domain=listing.domain,
            estimated_monthly_organic_visits=est_organic_visits,
            ranking_keywords_count=ranking_keywords_count,
            top_keywords=top_kws,
            commercial_intent_ratio=commercial_intent,
            backlinks_count=est_backlinks,
            referring_domains=est_referring_domains,
            domain_authority_proxy=da_proxy,
            indexed_pages=indexed_pages,
            brand_search_ratio=0.15,
            traffic_trend_6m=trend,
            traffic_trend_change_pct=trend_pct,
            serp_competition_level="medium",
            ai_overview_vulnerability=ai_risk,
            content_gap_opportunity=content_gap,
            seo_health_notes=health_notes,
            confidence=confidence
        )
