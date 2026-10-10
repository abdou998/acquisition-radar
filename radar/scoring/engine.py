"""
100-Point Scoring Engine & Opportunity Classifier.
Applies the rigorous acquisition rubric, deduction penalties, and generates buyer shortlists,
watchlists, and qualified exceptional candidates.
"""

from typing import List, Dict, Any, Tuple
from radar.models import Listing, SEOMetrics, Valuation, ScoreBreakdown
from radar.config import config

class ScoringEngine:
    @classmethod
    def evaluate(cls, listing: Listing, seo: SEOMetrics, valuation: Valuation) -> ScoreBreakdown:
        # Category 1: Existing Audience & Traffic Quality (max 25)
        aud_score = cls._score_audience(listing, seo)

        # Category 2: SEO Strength & Organic Growth Opportunities (max 20)
        seo_score = cls._score_seo(listing, seo)

        # Category 3: Revenue Quality & Financial Evidence (max 20)
        fin_score = cls._score_financial(listing, valuation)

        # Category 4: Price Attractiveness & Potential Return (max 15)
        price_score = cls._score_price(listing, valuation)

        # Category 5: Ease of Transfer & Operational Simplicity (max 10)
        trans_score = cls._score_transfer(listing, valuation)

        # Category 6: Risk Profile & Data Confidence (max 10)
        risk_score = cls._score_risk(listing, seo, valuation)

        # Penalties calculation
        penalties, penalty_reasons = cls._calculate_penalties(listing, seo, valuation)

        raw_total = aud_score + seo_score + fin_score + price_score + trans_score + risk_score
        final_total = max(0.0, min(100.0, round(raw_total - penalties, 1)))

        # Classification
        classification, rejection_reasons, is_exceptional, exceptional_just = cls._classify(
            final_total, listing, seo, valuation, penalty_reasons
        )

        return ScoreBreakdown(
            listing_id=listing.id,
            audience_score=round(aud_score, 1),
            seo_score=round(seo_score, 1),
            financial_score=round(fin_score, 1),
            price_score=round(price_score, 1),
            transfer_score=round(trans_score, 1),
            risk_score=round(risk_score, 1),
            penalties=round(penalties, 1),
            penalty_reasons=penalty_reasons,
            total_score=final_total,
            classification=classification,
            rejection_reasons=rejection_reasons,
            exceptional_5k_candidate=is_exceptional,
            exceptional_justification=exceptional_just
        )

    @staticmethod
    def _score_audience(listing: Listing, seo: SEOMetrics) -> float:
        score = 0.0
        visits = max(listing.monthly_visitors, listing.monthly_search_clicks)
        subs = listing.subscribers_count

        # Monthly traffic volume (max 14 pts)
        if visits >= 10000:
            score += 14.0
        elif visits >= 5000:
            score += 12.0
        elif visits >= 2000:
            score += 10.0
        elif visits >= 1000:
            score += 8.0
        elif visits >= 300:
            score += 5.0
        elif visits >= 100:
            score += 3.0

        # Owned audience (subscribers) (max 6 pts)
        if subs >= 2000:
            score += 6.0
        elif subs >= 800:
            score += 5.0
        elif subs >= 300:
            score += 3.5
        elif subs >= 100:
            score += 2.0

        # Verification credibility bonus (max 5 pts)
        if listing.seller_claims_verified or seo.confidence == "verified":
            score += 5.0
        elif seo.confidence == "high":
            score += 3.0
        elif seo.confidence == "medium":
            score += 1.5

        return min(25.0, score)

    @staticmethod
    def _score_seo(listing: Listing, seo: SEOMetrics) -> float:
        score = 0.0

        # Domain age and foundation (max 6 pts)
        if listing.domain_age_years >= 3.0:
            score += 6.0
        elif listing.domain_age_years >= 1.5:
            score += 4.5
        elif listing.domain_age_years >= 0.8:
            score += 3.0
        else:
            score += 1.5

        # Commercial search intent & rankings (max 5 pts)
        if seo.commercial_intent_ratio >= 0.50:
            score += 5.0
        elif seo.commercial_intent_ratio >= 0.30:
            score += 3.5
        else:
            score += 2.0

        # Resilience to AI Overviews / Zero-Click (max 4 pts)
        if seo.ai_overview_vulnerability == "low":
            score += 4.0
        elif seo.ai_overview_vulnerability == "medium":
            score += 2.5
        else:
            score += 1.0

        # Growth potential & backlink profile (max 5 pts)
        if seo.referring_domains >= 20:
            score += 5.0
        elif seo.referring_domains >= 8:
            score += 3.5
        else:
            score += 2.0

        return min(20.0, score)

    @staticmethod
    def _score_financial(listing: Listing, valuation: Valuation) -> float:
        score = 0.0
        profit = listing.monthly_profit
        rev = listing.monthly_revenue

        # Proven cash flow (max 10 pts)
        if profit >= 200:
            score += 10.0
        elif profit >= 100:
            score += 8.5
        elif profit >= 40:
            score += 6.5
        elif profit > 0:
            score += 4.5
        elif rev > 0:
            score += 3.5
        else:
            # $0 profit but high monetization potential
            if valuation.monetization_potential_base >= 100:
                score += 5.0
            elif valuation.monetization_potential_base >= 40:
                score += 3.0
            else:
                score += 1.0

        # Verification proof (max 5 pts)
        if listing.seller_claims_verified:
            score += 5.0
        elif profit == 0 and rev == 0:
            score += 3.0 # No false financial claims
        else:
            score += 1.0

        # Business model stability (recurring vs ad/affiliate) (max 5 pts)
        if listing.category in ["Micro-SaaS", "Community"]:
            score += 5.0
        elif listing.category in ["Tool/Utility", "Newsletter"]:
            score += 4.0
        else:
            score += 3.0

        return min(20.0, score)

    @staticmethod
    def _score_price(listing: Listing, valuation: Valuation) -> float:
        score = 0.0
        price = listing.asking_price
        payback = valuation.payback_period_months_conservative

        # Budget fit (max 5 pts)
        if price <= 500:
            score += 5.0
        elif price <= 1000:
            score += 4.0
        elif price <= 2500:
            score += 2.5
        elif price <= 5000:
            score += 1.5

        # Payback period (max 5 pts)
        if payback <= 6.0:
            score += 5.0
        elif payback <= 12.0:
            score += 4.0
        elif payback <= 18.0:
            score += 2.5
        elif payback <= 36.0:
            score += 1.5
        else:
            score += 0.5

        # Discount relative to rebuild replacement cost (max 5 pts)
        if valuation.rebuild_cost_estimate > 0:
            discount_ratio = 1.0 - (price / valuation.rebuild_cost_estimate)
            if discount_ratio >= 0.65:
                score += 5.0
            elif discount_ratio >= 0.40:
                score += 3.5
            elif discount_ratio >= 0.10:
                score += 2.0
            else:
                score += 1.0

        return min(15.0, score)

    @staticmethod
    def _score_transfer(listing: Listing, valuation: Valuation) -> float:
        score = 0.0

        # Low operating time commitment (max 5 pts)
        if valuation.estimated_weekly_hours <= 3.0:
            score += 5.0
        elif valuation.estimated_weekly_hours <= 6.0:
            score += 3.5
        else:
            score += 2.0

        # Tech stack & asset transferability (max 5 pts)
        stack = listing.tech_stack.lower()
        if any(s in stack for s in ["html", "static", "python", "fastapi", "react", "next.js", "wordpress", "php", "sqlite", "tailwind"]):
            score += 5.0
        elif stack == "unknown":
            score += 3.0
        else:
            score += 3.5

        return min(10.0, score)

    @staticmethod
    def _score_risk(listing: Listing, seo: SEOMetrics, valuation: Valuation) -> float:
        score = 10.0
        # Deduct for red flags
        flag_count = len(valuation.red_flags)
        score -= min(6.0, flag_count * 2.0)

        # Deduct if data confidence is low
        if seo.confidence == "low" and not listing.seller_claims_verified:
            score -= 2.0

        return max(0.0, score)

    @classmethod
    def _calculate_penalties(cls, listing: Listing, seo: SEOMetrics, valuation: Valuation) -> Tuple[float, List[str]]:
        penalties = 0.0
        reasons = []

        # 1. Declining traffic >30% over 6 months (-15 pts)
        if seo.traffic_trend_6m == "declining" or seo.traffic_trend_change_pct <= -30.0:
            penalties += 15.0
            reasons.append("Severe traffic decline (>30% loss) indicates potential Google search penalty (-15 pts).")

        # 2. Unverifiable revenue claims / suspicious spikes (-10 pts)
        if listing.monthly_revenue > 250 and not listing.seller_claims_verified:
            penalties += 10.0
            reasons.append("Unverified claimed revenue exceeding $250/mo without payment proof (-10 pts).")

        # 3. High red flag count (-10 pts)
        if len(valuation.red_flags) >= 2:
            penalties += 10.0
            reasons.append("Multiple due diligence red flags identified (-10 pts).")

        # 4. Personal brand attachment (-15 pts)
        if any("Personal brand" in f for f in valuation.red_flags):
            penalties += 15.0
            reasons.append("High personal brand dependency (-15 pts).")

        return penalties, reasons

    @classmethod
    def _classify(
        cls,
        total_score: float,
        listing: Listing,
        seo: SEOMetrics,
        valuation: Valuation,
        penalties: List[str]
    ) -> Tuple[str, List[str], bool, Dict[str, str]]:
        rejection_reasons = []
        is_exceptional = False
        exceptional_just = {}

        # Critical disqualifiers
        if listing.asking_price > config.max_exceptional_budget_usd:
            rejection_reasons.append(f"Asking price (${listing.asking_price:,.0f}) exceeds maximum allowable exceptional limit (${config.max_exceptional_budget_usd:,.0f}).")
            return "REJECTED", rejection_reasons, False, {}

        if any("Platform policy risk" in f for f in valuation.red_flags):
            rejection_reasons.append("Severe legal/platform risk: relies on scraping or unauthorized private APIs.")
            return "REJECTED", rejection_reasons, False, {}

        # Normal Budget <= $1,000 Candidates
        if listing.asking_price <= config.max_normal_budget_usd:
            if total_score >= config.shortlist_score_threshold:
                return "BUYER_SHORTLIST", [], False, {}
            elif total_score >= config.watchlist_score_threshold:
                return "WATCHLIST", [], False, {}
            else:
                rejection_reasons.append(f"Score {total_score:.1f} is below minimum quality threshold ({config.watchlist_score_threshold}).")
                if penalties:
                    rejection_reasons.extend(penalties)
                return "REJECTED", rejection_reasons, False, {}

        # Between $1,000 and $5,000: Candidate for Exceptional $5k Section
        else:
            # Stricter high bar for exceptional $5k candidate:
            # Score >= 76, verified or strong traffic, and demonstrable cash flow or established audience
            visits = max(listing.monthly_visitors, listing.monthly_search_clicks)
            is_cash_flowing = listing.monthly_profit >= 75.0 or (listing.monthly_revenue >= 150.0 and listing.seller_claims_verified)
            has_strong_audience = visits >= 3000 or listing.subscribers_count >= 1500

            if total_score >= 75.0 and (is_cash_flowing or has_strong_audience) and len(valuation.red_flags) <= 1:
                is_exceptional = True
                exceptional_just = {
                    "reason_to_exceed_budget": (
                        f"Trades at ${listing.asking_price:,.0f} with proven cash flow (${listing.monthly_profit:,.0f}/mo) "
                        f"and {visits:,} monthly visitors, representing an exceptional {valuation.payback_period_months_base:.1f}-month base payback."
                    ),
                    "evidence_validation": (
                        f"Verified financials: {listing.seller_claims_verified} | Domain age: {listing.domain_age_years:.1f} yrs | "
                        f"Audience: {visits:,} visits, {listing.subscribers_count:,} subscribers."
                    ),
                    "price_attractiveness": (
                        f"Valuation multiple of {valuation.valuation_multiple}x annual earnings vs industry typical 2.5x-4.0x. "
                        f"Trades at a {(1.0 - listing.asking_price / max(1.0, valuation.rebuild_cost_estimate))*100:.0f}% discount to rebuild cost."
                    ),
                    "downside_risks": (
                        "Customer churn upon founder departure, niche competition, or platform dependency."
                    ),
                    "required_verification": (
                        "Obtain 12-month verified Stripe/payment processor CSV export and conduct a 30-minute code/operations walkthrough with seller."
                    ),
                    "why_superior_to_sub_1k": (
                        f"Unlike sub-$1,000 starter assets, this generates immediate defensible positive cash flow (${listing.monthly_profit:,.0f}/mo) "
                        f"and has an established, de-risked organic customer base."
                    )
                }
                return "BUYER_SHORTLIST", [], True, exceptional_just
            elif total_score >= 60.0:
                return "WATCHLIST", [f"Priced above $1,000 (${listing.asking_price:,.0f}). Placed on Watchlist to monitor for price reductions."], False, {}
            else:
                rejection_reasons.append(f"Priced at ${listing.asking_price:,.0f} (> $1,000 normal budget) without meeting exceptional criteria.")
                return "REJECTED", rejection_reasons, False, {}
