"""
Unit tests for SQLite database layer and price history tracking.
"""

import os
import pytest
from radar.database import Database
from radar.models import Listing, SEOMetrics, Valuation, ScoreBreakdown

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_radar.db"
    return Database(str(db_file))

def test_listing_upsert_and_price_drop(test_db):
    l1 = Listing(
        id="test_l1",
        source="little_exits",
        external_id="101",
        url="https://littleexits.com/p/101",
        title="Test Tool",
        description="A great tool",
        category="Tool/Utility",
        asking_price=800.0,
        currency="USD"
    )

    persisted, is_new, price_changed = test_db.upsert_listing(l1)
    assert is_new is True
    assert price_changed is False
    assert test_db.count_active_listings() == 1

    # Price reduction simulation
    l1.asking_price = 650.0
    persisted_updated, is_new2, price_changed2 = test_db.upsert_listing(l1)
    assert is_new2 is False
    assert price_changed2 is True
    assert persisted_updated.status == "price_reduced"
    assert persisted_updated.price_change_amount == -150.0

    history = test_db.get_price_history("test_l1")
    assert len(history) == 2
    assert history[0]["price"] == 800.0
    assert history[1]["price"] == 650.0

def test_complete_opportunity_roundtrip(test_db):
    l = Listing(
        id="opp_1",
        source="motion_invest",
        external_id="m1",
        url="https://motioninvest.com/p/1",
        title="Affiliate Site",
        description="Reviews",
        category="Content/Blog",
        asking_price=900.0
    )
    test_db.upsert_listing(l)

    seo = SEOMetrics(listing_id="opp_1", domain="test.com", estimated_monthly_organic_visits=1500)
    test_db.save_seo(seo)

    val = Valuation(listing_id="opp_1", total_acquisition_cost=950.0, payback_period_months_conservative=10.0)
    test_db.save_valuation(val)

    score = ScoreBreakdown(listing_id="opp_1", total_score=78.0, classification="BUYER_SHORTLIST")
    test_db.save_score(score)

    retrieved = test_db.get_complete_opportunity("opp_1")
    assert retrieved is not None
    assert retrieved.listing.id == "opp_1"
    assert retrieved.seo.estimated_monthly_organic_visits == 1500
    assert retrieved.valuation.total_acquisition_cost == 950.0
    assert retrieved.score.total_score == 78.0
    assert retrieved.score.classification == "BUYER_SHORTLIST"
