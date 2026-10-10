"""
Traffic and Audience Valuation Engine.
Calculates low, base, and high scenarios for ad-equivalent search traffic value,
realistic monetization potential, and rebuild replacement cost.
"""

from typing import Dict, Any, Tuple, Optional
from radar.models import Listing, SEOMetrics
from radar.seo.cpc_benchmarks import get_niche_benchmark

class TrafficValuator:
    @staticmethod
    def calculate_ad_equivalent_value(visits: int, benchmark: Dict[str, Any], commercial_intent: float) -> Tuple[float, float, float]:
        """
        Estimates what an advertiser would pay Google Ads for this search traffic volume.
        Ad Value = Visits * CPC * Commercial Intent Weight.
        Returns: (low, base, high) in USD/month.
        """
        if visits <= 0:
            return 0.0, 0.0, 0.0

        # High-intent visits generate ad clicks or immediate demand
        effective_clicks = max(1.0, visits * commercial_intent * 0.12)

        low = round(effective_clicks * benchmark["cpc_low"], 2)
        base = round(effective_clicks * benchmark["cpc_base"], 2)
        high = round(effective_clicks * benchmark["cpc_high"], 2)

        return low, base, high

    @staticmethod
    def calculate_monetization_potential(
        listing: Listing, benchmark: Dict[str, Any], verified_visits: Optional[int] = None
    ) -> Tuple[float, float, float]:
        """
        Calculates realistic achievable monthly revenue if properly monetized:
        Combines display ads (RPM), affiliate sales, and digital product/SaaS conversion.
        Returns: (low, base, high) in USD/month.
        """
        if verified_visits is not None:
            visits = verified_visits
        else:
            visits = max(listing.monthly_visitors, listing.monthly_search_clicks)
        subscribers = listing.subscribers_count

        if visits <= 0 and subscribers <= 0:
            return 0.0, 0.0, 0.0

        # 1. Display Ad Potential (AdSense, Journey by Mediavine, etc.)
        rpm_low = benchmark["display_rpm_low"]
        rpm_base = benchmark["display_rpm_base"]
        rpm_high = benchmark["display_rpm_high"]

        ad_rev_low = (visits / 1000.0) * rpm_low
        ad_rev_base = (visits / 1000.0) * rpm_base
        ad_rev_high = (visits / 1000.0) * rpm_high

        # 2. Affiliate / Referral Potential
        aff_conv_pct = benchmark["affiliate_conversion_pct"] / 100.0
        aff_payout = benchmark["avg_affiliate_payout"]

        # Only a portion of visitors have buying intent
        buyer_visitors = visits * benchmark["default_commercial_intent"]
        aff_rev_base = buyer_visitors * aff_conv_pct * (aff_payout * 0.25)
        aff_rev_low = aff_rev_base * 0.4
        aff_rev_high = aff_rev_base * 2.0

        # 3. Newsletter Subscriber Value (if applicable)
        sub_rev_low = subscribers * 0.30   # $0.30 per active sub/month
        sub_rev_base = subscribers * 0.75  # $0.75 per active sub/month
        sub_rev_high = subscribers * 1.50

        # Combine based on business model
        if listing.category == "Newsletter":
            tot_low = sub_rev_low + (ad_rev_low * 0.2)
            tot_base = sub_rev_base + (ad_rev_base * 0.2)
            tot_high = sub_rev_high + (ad_rev_high * 0.2)
        elif listing.category in ["Micro-SaaS", "Tool/Utility"]:
            # Tool with traffic converting 0.5% - 2% to a $9 micro-plan or paid credits
            tool_paying_users_low = visits * 0.003
            tool_paying_users_base = visits * 0.008
            tool_paying_users_high = visits * 0.018

            tot_low = max(ad_rev_low, tool_paying_users_low * 7.0)
            tot_base = max(ad_rev_base, tool_paying_users_base * 9.0)
            tot_high = max(ad_rev_high, tool_paying_users_high * 15.0)
        else: # Content / Blog / Other
            tot_low = ad_rev_low + aff_rev_low
            tot_base = ad_rev_base + aff_rev_base
            tot_high = ad_rev_high + aff_rev_high

        # Blend with current proven revenue if seller already earns more
        if listing.monthly_revenue > 0:
            tot_low = max(tot_low, listing.monthly_revenue * 0.8)
            tot_base = max(tot_base, listing.monthly_revenue * 1.2)
            tot_high = max(tot_high, listing.monthly_revenue * 1.8)

        return round(tot_low, 2), round(tot_base, 2), round(tot_high, 2)

    @staticmethod
    def estimate_rebuild_cost(listing: Listing) -> Tuple[float, int]:
        """
        Estimates replacement cost and months required to build equivalent asset from scratch.
        Returns: (rebuild_cost_usd, rebuild_months)
        """
        category = listing.category
        visitors = max(listing.monthly_visitors, listing.monthly_search_clicks)

        # Baseline dev & setup costs
        if category in ["Micro-SaaS", "Tool/Utility"]:
            # MVP coding: 40-70 hours @ $35/hr = $1,400 - $2,500
            dev_cost = 1800.0
            base_months = 4
        elif category in ["Content/Blog"]:
            # 25 quality articles @ $40/article = $1,000 + site setup $300
            dev_cost = 1300.0
            base_months = 6
        elif category in ["Newsletter"]:
            # Setup + initial content + lead magnet
            dev_cost = 800.0
            base_months = 3
        else:
            dev_cost = 1000.0
            base_months = 4

        # SEO Sandbox and Audience Acquisition Cost to reach existing traffic
        # Reaching 1,000 monthly organic visitors takes ~6-9 months of Google indexing + $400 promotion/backlinks
        if visitors > 0:
            traffic_acquisition_cost = (visitors / 500.0) * 250.0
            total_rebuild_cost = dev_cost + min(5000.0, traffic_acquisition_cost)
            # Domain aging timeline
            extra_months = min(8, int(visitors / 1500) + 2)
            total_months = base_months + extra_months
        else:
            total_rebuild_cost = dev_cost
            total_months = base_months

        return round(total_rebuild_cost, 2), total_months
