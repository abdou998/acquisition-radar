"""
Undervaluation Thesis & 30-Day Turnaround Plan Engine.
Diagnoses monetization gaps, structural pricing inefficiencies, SEO quick wins,
and constructs actionable 30-day playbooks with explicit upside scenarios and risk disclosures.
"""

from typing import List, Dict, Any, Tuple
from radar.models import Listing, SEOMetrics

class ThesisGenerator:
    @classmethod
    def generate(cls, listing: Listing, seo: SEOMetrics, rebuild_cost: float, potential_base_rev: float) -> Tuple[str, List[str], float, float]:
        """
        Generates undervaluation thesis, 30-day action plan, estimated improvement cost, and weekly hours.
        Returns: (thesis_text, action_plan, improvement_cost_usd, weekly_hours)
        """
        category = listing.category
        visitors = max(listing.monthly_visitors, listing.monthly_search_clicks)
        price = listing.asking_price
        rev = listing.monthly_revenue

        thesis_points = []
        action_plan = []
        improvement_cost = 50.0  # Baseline hosting/domain renewal
        weekly_hours = 4.0

        # Scenario 1: Unmonetized or Poorly Monetized Traffic (Arbitrage)
        if visitors >= 500 and rev <= 20:
            thesis_points.append(
                f"MONETIZATION ARBITRAGE: The site attracts ~{visitors:,} monthly visitors but earns only ${rev:.0f}/mo. "
                f"The seller has neglected basic revenue capture. Installing targeted display ads (AdSense/Journey) "
                f"and contextually relevant affiliate links could generate ${potential_base_rev:.0f}/mo with near-zero ongoing overhead."
            )
            action_plan.extend([
                "Day 1-7: Complete domain and DNS migration. Integrate Cloudflare for security and performance.",
                "Day 8-14: Place clean, non-intrusive display ad units in header and mid-content.",
                "Day 15-21: Add comparison tables and affiliate partner recommendations for top high-traffic pages.",
                "Day 22-30: Implement email capture exit-intent popup offering a free niche cheat sheet/resource."
            ])
            improvement_cost = 60.0
            weekly_hours = 3.5

        # Scenario 2: Useful Micro-Tool / Utility with No Commercial Gate
        elif category in ["Tool/Utility", "Micro-SaaS"] and visitors >= 200:
            thesis_points.append(
                f"PRODUCT UTILITY UPGRADE: The tool has proven product-market utility with {visitors:,} monthly visits, "
                f"yet operates as a completely free utility or underpriced hobby project. "
                f"By adding a 'Pro' export tier (e.g. batch processing, watermark removal, or higher rate limits at $9-$19/mo) "
                f"or a pay-what-you-want option, even a conservative 1% conversion yields direct recurring cash flow."
            )
            action_plan.extend([
                "Day 1-7: Audit codebase and refactor environment secrets; migrate to cost-effective serverless hosting (e.g. Vercel/Fly.io/Cloudflare Pages).",
                "Day 8-14: Integrate Lemon Squeezy or Stripe checkout for a one-click Pro tier upgrade.",
                "Day 15-21: Launch on ProductHunt, HackerNews 'Show HN', and niche tool directories (There's An AI For That, Toolify).",
                "Day 22-30: Add a newsletter capture box providing weekly tips/updates to build an owned audience asset."
            ])
            improvement_cost = 75.0
            weekly_hours = 5.0

        # Scenario 3: Newsletter with Engaged Audience but Missing Sponsorships
        elif category == "Newsletter" and listing.subscribers_count >= 300:
            subs = listing.subscribers_count
            thesis_points.append(
                f"NEWSLETTER SPONSORSHIP GAP: An owned audience of {subs:,} subscribers represents an established trust asset. "
                f"At standard niche newsletter CPMs ($30-$50 per 1,000 opens), regular sponsored placements in bi-weekly issues "
                f"can readily produce $50-$150/month in high-margin sponsorship revenue."
            )
            action_plan.extend([
                "Day 1-7: Migrate subscriber list to Beehiiv or Substack; run a re-engagement welcome email.",
                "Day 8-14: Create a dedicated 'Sponsor This Newsletter' media kit page via Passionfroot or Notion.",
                "Day 15-21: Cold pitch 15 complementary SaaS and agency businesses in the niche offering introductory sponsor slots.",
                "Day 22-30: Introduce curated affiliate recommendations in the 'Tool of the Week' newsletter section."
            ])
            improvement_cost = 40.0
            weekly_hours = 3.0

        # Scenario 4: Neglected Content Asset with Established Authority
        elif category in ["Content/Blog"] and listing.domain_age_years >= 1.5:
            thesis_points.append(
                f"SEO REFRESH & CONTENT DEFROST: The domain is {listing.domain_age_years:.1f} years old with established indexation "
                f"and backlinks, but suffers from neglected, outdated content. Updating top 5 articles with fresh data, "
                f"fixing broken internal links, and modernizing layout can rapidly lift search impressions."
            )
            action_plan.extend([
                "Day 1-7: Complete transfer to lightweight WordPress or Ghost engine; compress images and optimize Core Web Vitals.",
                "Day 8-14: Identify top 10 historical traffic pages in GSC; update headers, refresh outdated links and statistics.",
                "Day 15-21: Create a hub-and-spoke internal linking architecture connecting all orphan articles.",
                "Day 22-30: Pitch 5 niche podcast/blog roundups for fresh editorial backlinks."
            ])
            improvement_cost = 80.0
            weekly_hours = 4.0

        # Default / Broad Fallback Thesis
        else:
            thesis_points.append(
                f"DISCOUNTED REPLACEMENT PLAY: Priced at ${price:.0f}, this asset trades well below its estimated "
                f"rebuild cost of ~${rebuild_cost:.0f}. Acquiring the established domain history, code, and existing search presence "
                f"bypasses the 6-month Google sandbox and setup friction."
            )
            action_plan.extend([
                "Day 1-7: Secure domain, repository, and asset credentials.",
                "Day 8-14: Fix UI usability bottlenecks and mobile responsive layout.",
                "Day 15-21: Implement Google Analytics 4, Search Console, and basic AdSense/affiliate tracking.",
                "Day 22-30: Begin targeted distribution across relevant subreddits, communities, and directory submissions."
            ])
            improvement_cost = 50.0
            weekly_hours = 4.0

        thesis_text = " ".join(thesis_points)
        return thesis_text, action_plan, improvement_cost, weekly_hours
