"""
Unit tests for Normalizer and Deduplicator engines.
"""

import pytest
from radar.models import Listing
from radar.core.normalizer import ListingNormalizer
from radar.core.deduplicator import Deduplicator

def test_price_normalization():
    assert ListingNormalizer.normalize_price("$750")[0] == 750.0
    assert ListingNormalizer.normalize_price("1,200 USD")[0] == 1200.0
    assert ListingNormalizer.normalize_price("€500")[0] == 540.0 # 500 * 1.08
    assert ListingNormalizer.normalize_price(850)[0] == 850.0
    assert ListingNormalizer.normalize_price(None)[0] == 0.0

def test_domain_extraction():
    assert ListingNormalizer.extract_domain("https://www.example.com/path?arg=1") == "example.com"
    assert ListingNormalizer.extract_domain("Check out my site at toolhub.dev today") == "toolhub.dev"
    assert ListingNormalizer.extract_domain("https://flippa.com/listings/12345") is None # Excludes marketplace domains

def test_metric_parsing():
    assert ListingNormalizer.parse_numeric_metric("12.5k") == 12500
    assert ListingNormalizer.parse_numeric_metric("1.2M") == 1200000
    assert ListingNormalizer.parse_numeric_metric("500") == 500
    assert ListingNormalizer.parse_numeric_metric(250) == 250

def test_category_normalization():
    assert ListingNormalizer.categorize_listing("My Chrome Extension", "SaaS tool for developers") == "Micro-SaaS"
    assert ListingNormalizer.categorize_listing("Niche Amazon Affiliate Blog", "Articles on pet care") == "Content/Blog"
    assert ListingNormalizer.categorize_listing("Online Loan Calculator", "Free financial calculator") == "Tool/Utility"
    assert ListingNormalizer.categorize_listing("Substack Newsletter on AI", "Weekly email list with 500 readers") == "Newsletter"

def test_deduplication_exact_domain():
    l1 = Listing(
        id="1", source="flippa", external_id="f1", url="https://flippa.com/1",
        title="Keyframe Tool", description="CSS tool", category="Tool/Utility",
        asking_price=700.0, domain="keyframe.dev"
    )
    l2 = Listing(
        id="2", source="sideprojectors", external_id="s1", url="https://sideprojectors.com/1",
        title="CSS Keyframe Generator", description="Online tool", category="Tool/Utility",
        asking_price=650.0, domain="keyframe.dev"
    )

    is_dup, reason = Deduplicator.are_duplicates(l1, l2)
    assert is_dup is True
    assert "domain" in reason.lower()

    # Batch test merges lower price
    merged = Deduplicator.deduplicate_batch([l1, l2])
    assert len(merged) == 1
    assert merged[0].asking_price == 650.0
    assert "sideprojectors" in merged[0].raw_metadata.get("cross_sources", [])
