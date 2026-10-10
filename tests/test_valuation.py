"""
Unit tests for Traffic Valuation, Due Diligence, and Financial Calculations.
"""

import pytest
from radar.models import Listing, SEOMetrics
from radar.seo.cpc_benchmarks import get_niche_benchmark
from radar.valuation.traffic import TrafficValuator
from radar.valuation.financial import FinancialValuator
from radar.valuation.thesis import ThesisGenerator
from radar.valuation import ValuationEngine

def test_ad_equivalent_value_calculation():
    benchmark = get_niche_benchmark("Tool/Utility", "Calculator", "Online tool")
    visits = 5000
    commercial_intent = 0.40

    low, base, high = TrafficValuator.calculate_ad_equivalent_value(visits, benchmark, commercial_intent)
    assert low > 0
    assert low < base < high
    # Check bounds
    assert base == round(visits * commercial_intent * 0.12 * benchmark["cpc_base"], 2)

def test_all_in_cost_calculation():
    # Flippa fee + escrow + domain
    total, escrow, transfer = FinancialValuator.calculate_all_in_cost(800.0, "flippa")
    assert total > 800.0
    assert escrow >= 30.0
    assert transfer >= 15.0

def test_payback_periods():
    # Proven cash flow: $50/mo profit on $600 cost
    cons_m, base_m = FinancialValuator.calculate_payback_periods(600.0, 50.0, 80.0)
    assert base_m == 12.0
    assert cons_m > base_m

def test_red_flags_detection():
    # Suspicious: $500 revenue with 10 visitors
    listing = Listing(
        id="flag_test",
        source="flippa",
        external_id="123",
        url="http://test.com/1",
        title="Test Store",
        description="Dropshipping store",
        category="E-commerce",
        asking_price=2000.0,
        monthly_revenue=500.0,
        monthly_profit=495.0,
        monthly_visitors=10,
        seller_claims_verified=False
    )
    flags = FinancialValuator.identify_red_flags(listing)
    assert len(flags) >= 2
    assert any("High claimed revenue" in f for f in flags)
    assert any("Implausible 98%+" in f for f in flags)

def test_turnaround_thesis_generation():
    listing = Listing(
        id="thesis_test",
        source="little_exits",
        external_id="456",
        url="http://test.com/2",
        title="PDF Compress Tool",
        description="Free utility tool with 2,500 visitors/mo.",
        category="Tool/Utility",
        asking_price=500.0,
        monthly_revenue=0.0,
        monthly_visitors=2500
    )
    seo = SEOMetrics(listing_id="thesis_test")
    thesis, playbook, imp_cost, hours = ThesisGenerator.generate(listing, seo, 1500.0, 90.0)

    assert "MONETIZATION ARBITRAGE" in thesis or "PRODUCT UTILITY UPGRADE" in thesis
    assert len(playbook) == 4
    assert imp_cost > 0
    assert hours > 0
