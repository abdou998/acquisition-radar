"""
Valuation package orchestrator.
"""

from typing import Tuple
from radar.models import Listing, SEOMetrics, Valuation
from radar.seo.cpc_benchmarks import get_niche_benchmark
from radar.valuation.traffic import TrafficValuator
from radar.valuation.financial import FinancialValuator
from radar.valuation.thesis import ThesisGenerator

class ValuationEngine:
    @classmethod
    def evaluate(cls, listing: Listing, seo: SEOMetrics) -> Valuation:
        benchmark = get_niche_benchmark(listing.category, listing.title, listing.description)

        # 1. Traffic ad-equivalent value
        ad_low, ad_base, ad_high = TrafficValuator.calculate_ad_equivalent_value(
            max(listing.monthly_visitors, listing.monthly_search_clicks),
            benchmark,
            seo.commercial_intent_ratio
        )

        # 2. Monetization potential
        mon_low, mon_base, mon_high = TrafficValuator.calculate_monetization_potential(listing, benchmark)

        # 3. Rebuild cost
        rebuild_cost, rebuild_months = TrafficValuator.estimate_rebuild_cost(listing)

        # 4. All-in acquisition cost
        total_cost, escrow_fee, transfer_fee = FinancialValuator.calculate_all_in_cost(listing.asking_price, listing.source)

        # 5. Multiple calculation
        multiple = 0.0
        if listing.monthly_profit > 0:
            multiple = round(listing.asking_price / (listing.monthly_profit * 12.0), 2)
        elif listing.monthly_revenue > 0:
            multiple = round(listing.asking_price / (listing.monthly_revenue * 12.0), 2)

        # 6. Payback period
        cons_payback, base_payback = FinancialValuator.calculate_payback_periods(total_cost, listing.monthly_profit, mon_base)

        # 7. Red flags & diligence
        red_flags = FinancialValuator.identify_red_flags(listing)
        checklist = FinancialValuator.generate_diligence_checklist(listing)

        # 8. Undervaluation thesis & action plan
        thesis, action_plan, imp_cost, weekly_hours = ThesisGenerator.generate(listing, seo, rebuild_cost, mon_base)

        return Valuation(
            listing_id=listing.id,
            total_acquisition_cost=total_cost,
            escrow_fee_estimate=escrow_fee,
            transfer_fee_estimate=transfer_fee,
            ad_equivalent_value_low=ad_low,
            ad_equivalent_value_base=ad_base,
            ad_equivalent_value_high=ad_high,
            monetization_potential_low=mon_low,
            monetization_potential_base=mon_base,
            monetization_potential_high=mon_high,
            rebuild_cost_estimate=rebuild_cost,
            rebuild_months_estimate=rebuild_months,
            valuation_multiple=multiple,
            payback_period_months_conservative=cons_payback,
            payback_period_months_base=base_payback,
            undervaluation_thesis=thesis,
            action_plan_30_days=action_plan,
            estimated_improvement_cost=imp_cost,
            estimated_weekly_hours=weekly_hours,
            due_diligence_checklist=checklist,
            red_flags=red_flags
        )
