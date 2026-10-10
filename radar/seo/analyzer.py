"""
SEO Intelligence Engine.
Evaluates organic search visibility, Google algorithm risk, search intent,
AI Overviews vulnerability, and keyword expansion opportunities based on Google Search Central guidelines.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from radar.models import Listing, SEOMetrics
from radar.seo.cpc_benchmarks import get_niche_benchmark

class SEOAnalyzer:
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
        # Check raw metadata for historical month data if provided by marketplace
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

        # If no explicit history array, examine description and seller claims
        desc = listing.description.lower()
        if "declining" in desc or "lost traffic" in desc or "algorithm update" in desc:
            return "declining", -35.0, "Seller notes traffic decline following search engine updates."
        if "growing" in desc or "increasing traffic" in desc:
            return "growing", 15.0, "Organic traffic reportedly increasing."

        return "stable", 0.0, "Baseline traffic assumed stable based on available current snapshot."

    @classmethod
    def analyze(cls, listing: Listing) -> SEOMetrics:
        """
        Runs comprehensive SEO assessment on a listing.
        """
        benchmark = get_niche_benchmark(listing.category, listing.title, listing.description)
        ai_risk, ai_risk_notes = cls.assess_ai_overview_vulnerability(listing.category, listing.title, listing.description)
        trend, trend_pct, trend_notes = cls.estimate_traffic_trend(listing)

        # Baseline organic visits estimate
        est_organic_visits = listing.monthly_visitors
        if est_organic_visits == 0 and listing.monthly_search_clicks > 0:
            est_organic_visits = listing.monthly_search_clicks

        # Determine confidence
        confidence = "low"
        if listing.seller_claims_verified:
            confidence = "verified"
        elif listing.domain and est_organic_visits > 0:
            confidence = "medium"

        # Referring domains and authority proxy estimation
        domain_age = listing.domain_age_years if listing.domain_age_years > 0 else 1.5
        est_referring_domains = max(5, int(domain_age * 12 + (est_organic_visits / 200)))
        est_backlinks = est_referring_domains * 7
        da_proxy = min(60.0, round(10.0 + (domain_age * 4.0) + (min(est_organic_visits, 10000) / 400.0), 1))

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

        health_notes = [
            f"AI Overviews Risk: {ai_risk.upper()} - {ai_risk_notes}",
            f"Traffic Trend: {trend.upper()} ({trend_notes})",
            f"Commercial Search Intent: {int(commercial_intent * 100)}% estimated transactional/commercial intent."
        ]

        if trend == "declining":
            health_notes.append("WARNING: Potential vulnerability to Google Helpful Content / Core Updates. Audit content quality before bidding.")

        return SEOMetrics(
            listing_id=listing.id,
            domain=listing.domain,
            estimated_monthly_organic_visits=est_organic_visits,
            ranking_keywords_count=max(10, int(est_organic_visits / 12)),
            top_keywords=top_kws,
            commercial_intent_ratio=commercial_intent,
            backlinks_count=est_backlinks,
            referring_domains=est_referring_domains,
            domain_authority_proxy=da_proxy,
            indexed_pages=max(5, int(domain_age * 15)),
            brand_search_ratio=0.15,
            traffic_trend_6m=trend,
            traffic_trend_change_pct=trend_pct,
            serp_competition_level="medium",
            ai_overview_vulnerability=ai_risk,
            content_gap_opportunity=content_gap,
            seo_health_notes=health_notes,
            confidence=confidence
        )
