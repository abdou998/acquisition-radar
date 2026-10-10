"""
Daily Acquisition Radar Report Generator.
Generates comprehensive Markdown and responsive HTML reports according to strict acquisition rubrics.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from radar.models import CompleteOpportunity, DailyRun
from radar.config import config

class ReportGenerator:
    def __init__(self):
        templates_dir = Path(__file__).resolve().parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True
        )

    @classmethod
    def generate_markdown(cls, run: DailyRun, opportunities: List[CompleteOpportunity]) -> str:
        shortlist_1k = [
            o for o in opportunities
            if o.score.classification == "BUYER_SHORTLIST" and not o.score.exceptional_5k_candidate and o.listing.asking_price <= config.max_normal_budget_usd
        ]
        exceptional_5k = [
            o for o in opportunities
            if o.score.exceptional_5k_candidate
        ]
        seo_highlights = [
            o for o in opportunities
            if o.score.seo_score >= 14.0 or o.seo.domain_authority_proxy >= 25.0
        ]
        watchlist_items = [
            o for o in opportunities
            if o.score.classification == "WATCHLIST" or o.listing.status == "price_reduced"
        ]

        # Determine single most interesting deal
        highlight_deal = None
        if shortlist_1k:
            highlight_deal = max(shortlist_1k, key=lambda x: x.score.total_score)
        elif exceptional_5k:
            highlight_deal = max(exceptional_5k, key=lambda x: x.score.total_score)

        lines = []
        lines.append(f"# Daily Undervalued Online Business Acquisition Radar")
        lines.append(f"**Report Date:** {run.run_date} | **Generated At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | **Schedule:** 08:00 {config.schedule_timezone}\n")
        lines.append("---\n")

        # ==========================================
        # SECTION A: EXECUTIVE SUMMARY
        # ==========================================
        lines.append("## A. Executive Summary\n")
        lines.append(f"- **Total Listings Audited Today:** {run.total_discovered}")
        lines.append(f"- **Promising Candidates Identified:** {len(shortlist_1k) + len(exceptional_5k)}")
        lines.append(f"- **Strong Candidates Under $1,000 Budget:** {len(shortlist_1k)}")
        lines.append(f"- **Significant Price Reductions / Changes:** {run.price_reductions_count}")
        lines.append(f"- **Watchlist Monitored:** {len(watchlist_items)}")

        if highlight_deal:
            l = highlight_deal.listing
            s = highlight_deal.score
            v = highlight_deal.valuation
            lines.append(f"\n> **Top Opportunity of the Day:** **[{l.title}]({l.url})**  ")
            lines.append(f"> **Price:** ${l.asking_price:,.0f} USD | **Score:** {s.total_score}/100 | **Source:** {l.source.title()}  ")
            lines.append(f"> **Why it stands out:** {v.undervaluation_thesis[:280]}...\n")
        else:
            lines.append("\n> **Top Opportunity of the Day:** No single breakthrough deal met the top-conviction threshold today. Maintaining disciplined capital allocation.\n")

        lines.append("---\n")

        # ==========================================
        # SECTION B: BEST OPPORTUNITIES UNDER $1,000
        # ==========================================
        lines.append("## B. Best Opportunities Under $1,000\n")
        lines.append(f"*Normal maximum budget: ${config.max_normal_budget_usd:,.0f} total, inclusive of transaction & transfer costs.*\n")

        if not shortlist_1k:
            lines.append("No candidates met the minimum score threshold (>= 70/100) within the $1,000 budget today. Avoiding low-quality filler listings.\n")
        else:
            for rank, opp in enumerate(shortlist_1k, start=1):
                l = opp.listing
                s = opp.score
                seo = opp.seo
                v = opp.valuation

                traffic_tag = "Verified (GA4/GSC)" if l.seller_claims_verified else "Seller-Reported"
                fin_tag = "Verified (Stripe/Bank)" if l.seller_claims_verified else "Seller-Reported"

                lines.append(f"### #{rank}. [{l.title}]({l.url})")
                lines.append(f"**Score:** `{s.total_score}/100` | **Classification:** `BUYER SHORTLIST` | **Confidence:** `{seo.confidence.upper()}`\n")

                lines.append("| Metric | Value | Data Source / Label |")
                lines.append("|---|---|---|")
                lines.append(f"| **Marketplace** | {l.source.title()} | [Direct Listing Link]({l.url}) |")
                lines.append(f"| **Asking Price** | **${l.asking_price:,.0f}** | Seller Listed |")
                lines.append(f"| **Estimated All-In Cost** | **${v.total_acquisition_cost:,.0f}** | Inferred (Price + ${v.escrow_fee_estimate:.0f} Escrow + ${v.transfer_fee_estimate:.0f} Transfer) |")
                lines.append(f"| **Business Model & Niche** | {l.category} | {l.domain or 'Domain masked'} |")
                lines.append(f"| **Monthly Organic Visits** | **{l.monthly_visitors:,} visits** | {traffic_tag} |")
                lines.append(f"| **Monthly Search Clicks** | {seo.estimated_monthly_organic_visits:,} clicks | Third-Party Estimated |")
                lines.append(f"| **Claimed Revenue / Profit** | ${l.monthly_revenue:,.0f} / ${l.monthly_profit:,.0f}/mo | {fin_tag} |")
                lines.append(f"| **Estimated Payback Period** | **{v.payback_period_months_conservative:.1f} months** | Conservative Cash Flow Model |")
                lines.append(f"| **Domain Age & Authority** | {l.domain_age_years:.1f} yrs (DA Proxy: {seo.domain_authority_proxy:.0f}) | Third-Party Estimated |")
                lines.append("")

                lines.append("#### Why This Opportunity Is Undervalued")
                lines.append(f"{v.undervaluation_thesis}\n")

                lines.append("#### Traffic Valuation (Advertising-Equivalent vs Commercial Cash Flow)")
                lines.append(f"- **Ad-Equivalent Traffic Value:** **${v.ad_equivalent_value_base:,.0f}/month** *(Low: ${v.ad_equivalent_value_low:,.0f} | High: ${v.ad_equivalent_value_high:,.0f})*")
                lines.append(f"  *Note: Ad-equivalent value represents what an advertiser would pay Google Ads for this search volume at prevailing niche CPCs. It is NOT current revenue.*")
                lines.append(f"- **Achievable Monetization Potential:** **${v.monetization_potential_base:,.0f}/month** *(via targeted affiliate partnerships & non-intrusive display ads)*")
                lines.append(f"- **Estimated Rebuild Cost & Time:** **${v.rebuild_cost_estimate:,.0f}** across **{v.rebuild_months_estimate} months** *(buying saves ~{v.rebuild_months_estimate} months of Google sandbox aging and build effort)*\n")

                lines.append("#### 30-Day Turnaround Playbook")
                for step in v.action_plan_30_days:
                    lines.append(f"- {step}")
                lines.append(f"- **Required Improvement Capital:** ~${v.estimated_improvement_cost:,.0f} | **Weekly Time Commitment:** ~{v.estimated_weekly_hours:.1f} hrs/week\n")

                lines.append("#### Key Risks & Pre-Purchase Due Diligence Checklist")
                if v.red_flags:
                    lines.append("**Potential Warning Flags:**")
                    for rf in v.red_flags:
                        lines.append(f"- ⚠️ {rf}")
                lines.append("**Mandatory Verification Steps:**")
                for item in v.due_diligence_checklist[:4]:
                    lines.append(f"- [ ] {item}")

                next_step = "Contact seller via marketplace messaging to request 12-month Google Analytics read-only access."
                lines.append(f"\n**Recommended Next Action:** `{next_step}`\n")
                lines.append("---\n")

        # ==========================================
        # SECTION C: BEST SEO OPPORTUNITIES
        # ==========================================
        lines.append("## C. Best SEO Opportunities\n")
        lines.append("*Digital assets with notable search presence, quality referring domains, or strong organic ranking moats.*\n")

        if not seo_highlights:
            lines.append("No specific assets stood out primarily on SEO criteria today.\n")
        else:
            for opp in seo_highlights[:3]:
                l = opp.listing
                seo = opp.seo
                lines.append(f"### [{l.title}]({l.url}) (`${l.asking_price:,.0f}` - {l.source.title()})")
                lines.append(f"- **Domain & Search Trajectory:** `{l.domain or 'Domain masked'}` | {l.domain_age_years:.1f} years old | Trend: **{seo.traffic_trend_6m.upper()}** ({seo.traffic_trend_change_pct:+.1f}%)")
                lines.append(f"- **Search Intent Quality:** {int(seo.commercial_intent_ratio * 100)}% commercial/transactional intent | Top terms: *{', '.join(seo.top_keywords[:3])}*")
                lines.append(f"- **AI Overviews Vulnerability:** `{seo.ai_overview_vulnerability.upper()}`")
                lines.append(f"- **Content Gap & Expansion Opportunity:** {seo.content_gap_opportunity}")
                lines.append(f"- **Promising Next Action:** Target commercial keyword comparison tables and update top 5 legacy pages with fresh rich snippets.\n")

        lines.append("---\n")

        # ==========================================
        # SECTION D: WATCHLIST AND MEANINGFUL CHANGES
        # ==========================================
        lines.append("## D. Watchlist and Price Changes\n")
        lines.append("*Tracked assets with recent price reductions, new evidence, or interesting metrics pending diligence.*\n")

        if not watchlist_items:
            lines.append("No significant price drops or status updates recorded across tracked listings today.\n")
        else:
            lines.append("| Listing | Category | Original | Current Asking | Price Change | Status / Notes |")
            lines.append("|---|---|---|---|---|---|")
            for opp in watchlist_items[:6]:
                l = opp.listing
                orig_str = f"${l.original_price:,.0f}" if l.original_price else "-"
                curr_str = f"${l.asking_price:,.0f}"
                delta_str = f"{l.price_change_percent:.1f}% (${l.price_change_amount:,.0f})" if l.price_change_amount != 0 else "Unchanged"
                status_str = "Price Reduced 📉" if l.price_change_amount < 0 else "Watchlist (Score: %d)" % int(opp.score.total_score)
                lines.append(f"| [{l.title[:35]}...]({l.url}) | {l.category} | {orig_str} | **{curr_str}** | {delta_str} | {status_str} |")
            lines.append("")

        lines.append("---\n")

        # ==========================================
        # SECTION E: WORTH CONSIDERING - EXCEPTIONAL UP TO $5,000
        # ==========================================
        lines.append("## E. Worth Considering — Exceptional Opportunities Up to $5,000\n")
        lines.append("*Strictly qualified opportunities that present compelling risk-adjusted value justifying an exception to the normal $1,000 budget.*\n")

        if not exceptional_5k:
            lines.append("> **“No exceptional opportunities justified exceeding the $1,000 budget today.”**\n")
            lines.append("All candidates between $1,000 and $5,000 reviewed today had either insufficient proven cash flow, unverifiable metrics, or high platform risks.\n")
        else:
            for opp in exceptional_5k:
                l = opp.listing
                s = opp.score
                v = opp.valuation
                seo = opp.seo
                just = s.exceptional_justification

                lines.append(f"### 🌟 EXCEPTIONAL CANDIDATE: [{l.title}]({l.url})")
                lines.append(f"**Asking Price:** **${l.asking_price:,.0f} USD** | **Score:** `{s.total_score}/100` | **Payback Period:** `{v.payback_period_months_base:.1f} months`\n")

                lines.append(f"1. **Why It Merits Exceeding the Normal Budget:**  \n   {just.get('reason_to_exceed_budget', 'Proven cash flow and defensive audience.')}\n")
                lines.append(f"2. **Evidence Validating Audience & Revenue:**  \n   {just.get('evidence_validation', 'Stripe connected and stable organic search.')}\n")
                lines.append(f"3. **Why the Price Appears Attractive:**  \n   {just.get('price_attractiveness', 'Trading well below typical multiples.')}\n")
                lines.append(f"4. **What Could Go Wrong:**  \n   {just.get('downside_risks', 'Potential churn or technical debt.')}\n")
                lines.append(f"5. **Required Verification Before Spending Money:**  \n   {just.get('required_verification', 'Live video screen-share of payment processor.')}\n")
                lines.append(f"6. **Why This is Materially Better Than Sub-$1,000 Alternatives:**  \n   {just.get('why_superior_to_sub_1k', 'Generates immediate profit and eliminates the 6-month launch risk.')}\n")

        lines.append("\n---\n")
        lines.append("*Daily Acquisition Radar is automated research. Always conduct independent due diligence, inspect live analytics, and use escrow before transferring funds.*")

        return "\n".join(lines)

    @classmethod
    def generate_html(cls, run: DailyRun, opportunities: List[CompleteOpportunity]) -> str:
        """
        Renders standalone responsive HTML report.
        """
        shortlist_1k = [
            o for o in opportunities
            if o.score.classification == "BUYER_SHORTLIST" and not o.score.exceptional_5k_candidate and o.listing.asking_price <= config.max_normal_budget_usd
        ]
        exceptional_5k = [
            o for o in opportunities
            if o.score.exceptional_5k_candidate
        ]
        seo_highlights = [
            o for o in opportunities
            if o.score.seo_score >= 14.0 or o.seo.domain_authority_proxy >= 25.0
        ]
        watchlist_items = [
            o for o in opportunities
            if o.score.classification == "WATCHLIST" or o.listing.status == "price_reduced"
        ]

        highlight_deal = shortlist_1k[0] if shortlist_1k else (exceptional_5k[0] if exceptional_5k else None)

        template_path = Path(__file__).resolve().parent / "templates" / "daily_report.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_str = f.read()
            from jinja2 import Template
            t = Template(template_str)
            return t.render(
                run=run,
                shortlist_1k=shortlist_1k,
                exceptional_5k=exceptional_5k,
                seo_highlights=seo_highlights,
                watchlist_items=watchlist_items,
                highlight_deal=highlight_deal,
                config=config,
                now_str=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            )
        else:
            # Fallback simple HTML
            md_content = cls.generate_markdown(run, opportunities)
            return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Acquisition Radar Report - {run.run_date}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1e293b; background: #f8fafc; }}
pre {{ background: #ffffff; padding: 25px; border-radius: 8px; border: 1px solid #e2e8f0; white-space: pre-wrap; }}
</style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>"""
