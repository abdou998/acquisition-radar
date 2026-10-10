"""
Unit tests for Report Generation (Markdown and HTML).
"""

import pytest
from radar.models import Listing, SEOMetrics, Valuation, ScoreBreakdown, CompleteOpportunity, DailyRun
from radar.reporting.generator import ReportGenerator

def test_report_generation_structure():
    run = DailyRun(
        run_id="run_test",
        run_date="2026-10-10",
        total_discovered=5,
        shortlist_count=1,
        watchlist_count=1,
        rejected_count=3,
        exceptional_5k_count=0
    )

    opp1 = CompleteOpportunity(
        listing=Listing(
            id="1", source="little_exits", external_id="1", url="http://test.com/1",
            title="CSS Keyframe Generator", description="Tool", category="Tool/Utility",
            asking_price=600.0, monthly_visitors=2500, domain="keyframe.dev"
        ),
        seo=SEOMetrics(listing_id="1", estimated_monthly_organic_visits=2500, confidence="verified"),
        valuation=Valuation(
            listing_id="1", total_acquisition_cost=650.0, payback_period_months_conservative=6.5,
            ad_equivalent_value_base=80.0, rebuild_cost_estimate=1500.0,
            undervaluation_thesis="Unmonetized organic traffic tool arbitrage."
        ),
        score=ScoreBreakdown(listing_id="1", total_score=82.0, classification="BUYER_SHORTLIST")
    )

    md = ReportGenerator.generate_markdown(run, [opp1])
    html = ReportGenerator.generate_html(run, [opp1])

    # Check that all 5 required sections are present
    assert "## A. Executive Summary" in md
    assert "## B. Best Opportunities Under $1,000" in md
    assert "## C. Best SEO Opportunities" in md
    assert "## D. Watchlist and Price Changes" in md
    assert "## E. Worth Considering — Exceptional Opportunities Up to $5,000" in md

    # Check explicit zero exceptional items message
    assert "No exceptional opportunities justified exceeding the $1,000 budget today" in md

    # Check HTML has valid markup and contains deal title
    assert "<!DOCTYPE html>" in html
    assert "CSS Keyframe Generator" in html
