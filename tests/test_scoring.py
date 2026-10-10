"""
Unit tests for 100-Point Scoring Engine and Opportunity Classifier.
"""

import pytest
from radar.models import Listing, SEOMetrics, Valuation
from radar.scoring.engine import ScoringEngine

def test_high_conviction_listing_scoring():
    listing = Listing(
        id="test_tool_1",
        source="little_exits",
        external_id="ext_1",
        url="https://littleexits.com/tool-1",
        title="SVG to CSS Keyframe Tool",
        description="Browser utility with 3,000 visitors/mo, unmonetized.",
        category="Tool/Utility",
        asking_price=600.0,
        monthly_visitors=3000,
        monthly_profit=15.0,
        domain="keyframe-test.dev",
        domain_age_years=2.0,
        seller_claims_verified=True
    )
    seo = SEOMetrics(
        listing_id="test_tool_1",
        domain="keyframe-test.dev",
        estimated_monthly_organic_visits=3000,
        commercial_intent_ratio=0.45,
        ai_overview_vulnerability="low",
        referring_domains=15,
        traffic_trend_6m="stable",
        confidence="verified"
    )
    valuation = Valuation(
        listing_id="test_tool_1",
        total_acquisition_cost=650.0,
        ad_equivalent_value_base=95.0,
        monetization_potential_base=75.0,
        rebuild_cost_estimate=1800.0,
        payback_period_months_conservative=8.5,
        payback_period_months_base=6.0
    )

    score = ScoringEngine.evaluate(listing, seo, valuation)
    assert score.total_score >= 70.0
    assert score.classification == "BUYER_SHORTLIST"
    assert not score.exceptional_5k_candidate
    assert score.penalties == 0.0

def test_penalty_for_declining_traffic():
    listing = Listing(
        id="test_penalized",
        source="flippa",
        external_id="ext_2",
        url="https://flippa.com/test-declining",
        title="Declining Meme Site",
        description="Lost traffic in recent update.",
        category="Content/Blog",
        asking_price=700.0,
        monthly_visitors=4000
    )
    seo = SEOMetrics(
        listing_id="test_penalized",
        traffic_trend_6m="declining",
        traffic_trend_change_pct=-45.0
    )
    valuation = Valuation(listing_id="test_penalized")

    score = ScoringEngine.evaluate(listing, seo, valuation)
    assert score.penalties >= 15.0
    assert any("traffic decline" in r.lower() for r in score.penalty_reasons)

def test_exceptional_5k_qualification():
    listing = Listing(
        id="test_exceptional",
        source="acquire",
        external_id="ext_3",
        url="https://acquire.com/test-saas",
        title="B2B Uptime Monitor SaaS",
        description="Profitable monitoring SaaS with 80 paying customers.",
        category="Micro-SaaS",
        asking_price=3500.0,
        monthly_revenue=300.0,
        monthly_profit=260.0,
        monthly_visitors=6000,
        domain="uptime-beacon.com",
        domain_age_years=3.5,
        seller_claims_verified=True
    )
    seo = SEOMetrics(
        listing_id="test_exceptional",
        domain="uptime-beacon.com",
        estimated_monthly_organic_visits=6000,
        ai_overview_vulnerability="low",
        referring_domains=25,
        confidence="verified"
    )
    valuation = Valuation(
        listing_id="test_exceptional",
        total_acquisition_cost=3650.0,
        rebuild_cost_estimate=4500.0,
        payback_period_months_base=14.0,
        valuation_multiple=1.12
    )

    score = ScoringEngine.evaluate(listing, seo, valuation)
    assert score.exceptional_5k_candidate is True
    assert score.classification == "BUYER_SHORTLIST"
    assert "reason_to_exceed_budget" in score.exceptional_justification
    assert "why_superior_to_sub_1k" in score.exceptional_justification

def test_rejected_over_budget_without_exceptional_moat():
    listing = Listing(
        id="test_over_budget",
        source="sideprojectors",
        external_id="ext_4",
        url="https://sideprojectors.com/test-4",
        title="Unproven App Idea",
        description="No traffic, no revenue, asking $2,500.",
        category="Micro-SaaS",
        asking_price=2500.0,
        monthly_revenue=0.0,
        monthly_visitors=50
    )
    seo = SEOMetrics(listing_id="test_over_budget")
    valuation = Valuation(listing_id="test_over_budget")

    score = ScoringEngine.evaluate(listing, seo, valuation)
    assert score.classification == "REJECTED"
    assert not score.exceptional_5k_candidate
