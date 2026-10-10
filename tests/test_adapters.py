"""
Unit tests for Marketplace Adapters and Registry.
"""

import pytest
from radar.adapters.registry import registry
from radar.adapters.flippa import FlippaAdapter
from radar.adapters.little_exits import LittleExitsAdapter
from radar.adapters.sideprojectors import SideProjectorsAdapter
from radar.adapters.motion_invest import MotionInvestAdapter
from radar.adapters.microns import MicronsAdapter
from radar.adapters.acquire import AcquireAdapter
from radar.adapters.investors_club import InvestorsClubAdapter

def test_adapters_documentation_coverage():
    docs = registry.list_sources_documentation()
    assert len(docs) == 7

    sources = [d["source"] for d in docs]
    assert "Flippa" in sources
    assert "Motion Invest" in sources
    assert "SideProjectors" in sources
    assert "Microns.io" in sources
    assert "Investors Club" in sources
    assert any("Little Exits" in s for s in sources)
    assert any("Acquire" in s for s in sources)

    for doc in docs:
        assert "inventory_profile" in doc
        assert "price_range_suitability" in doc
        assert "buyer_protection" in doc
        assert "access_method" in doc
        assert "access_restrictions" in doc

def test_registry_fetch_with_fixtures():
    import asyncio
    listings, summary = asyncio.run(registry.fetch_all(include_fixtures=True))
    assert len(listings) >= 5
    assert "curated_radar_feed" in summary
    assert summary["curated_radar_feed"]["status"] == "success"

    # Confirm unique URLs (deduplicated)
    urls = [l.url for l in listings]
    assert len(urls) == len(set(urls))
