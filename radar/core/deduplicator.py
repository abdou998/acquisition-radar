"""
Cross-marketplace deduplication engine.
Identifies identical or relisted digital assets across platforms.
"""

import re
from typing import List, Dict, Tuple, Optional
from radar.models import Listing

class Deduplicator:
    @staticmethod
    def _tokenize(text: str) -> set:
        cleaned = re.sub(r"[^\w\s]", "", text.lower())
        words = cleaned.split()
        stopwords = {"for", "sale", "a", "an", "the", "in", "with", "and", "or", "to", "of", "website", "online", "business", "project"}
        return {w for w in words if w not in stopwords and len(w) > 2}

    @classmethod
    def similarity_score(cls, title_a: str, title_b: str) -> float:
        tokens_a = cls._tokenize(title_a)
        tokens_b = cls._tokenize(title_b)
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return len(intersection) / len(union) if union else 0.0

    @classmethod
    def are_duplicates(cls, listing_a: Listing, listing_b: Listing) -> Tuple[bool, str]:
        """
        Determines if two listings represent the same underlying business.
        Returns (is_duplicate, reason).
        """
        if listing_a.id == listing_b.id or listing_a.url == listing_b.url:
            return True, "Identical listing URL/ID"

        # 1. Exact domain match (highest confidence)
        if listing_a.domain and listing_b.domain:
            if listing_a.domain.lower() == listing_b.domain.lower():
                return True, f"Identical domain match ({listing_a.domain})"

        # 2. High title similarity and close price (within 25%)
        sim = cls.similarity_score(listing_a.title, listing_b.title)
        if sim >= 0.70:
            price_ratio = min(listing_a.asking_price, listing_b.asking_price) / max(listing_a.asking_price, listing_b.asking_price) if max(listing_a.asking_price, listing_b.asking_price) > 0 else 1.0
            if price_ratio >= 0.75:
                return True, f"High title similarity ({sim:.2f}) and matching price range"

        return False, ""

    @classmethod
    def deduplicate_batch(cls, listings: List[Listing]) -> List[Listing]:
        """
        Filters a list of newly discovered listings, merging duplicates and preserving best data.
        """
        unique_listings: List[Listing] = []
        for candidate in listings:
            matched_idx = -1
            match_reason = ""
            for idx, existing in enumerate(unique_listings):
                is_dup, reason = cls.are_duplicates(candidate, existing)
                if is_dup:
                    matched_idx = idx
                    match_reason = reason
                    break

            if matched_idx == -1:
                unique_listings.append(candidate)
            else:
                existing = unique_listings[matched_idx]
                # Merge cross-listing info
                cross_sources = existing.raw_metadata.setdefault("cross_sources", [existing.source])
                if candidate.source not in cross_sources:
                    cross_sources.append(candidate.source)
                cross_urls = existing.raw_metadata.setdefault("cross_urls", [existing.url])
                if candidate.url not in cross_urls:
                    cross_urls.append(candidate.url)
                
                # If candidate has lower price, update asking price to lower arbitrage price
                if candidate.asking_price > 0 and (candidate.asking_price < existing.asking_price or existing.asking_price == 0):
                    existing.asking_price = candidate.asking_price

                # Enrich missing metrics
                if not existing.domain and candidate.domain:
                    existing.domain = candidate.domain
                if existing.monthly_visitors == 0 and candidate.monthly_visitors > 0:
                    existing.monthly_visitors = candidate.monthly_visitors
                if existing.monthly_revenue == 0 and candidate.monthly_revenue > 0:
                    existing.monthly_revenue = candidate.monthly_revenue
                if existing.monthly_profit == 0 and candidate.monthly_profit > 0:
                    existing.monthly_profit = candidate.monthly_profit
                if not existing.seller_claims_verified and candidate.seller_claims_verified:
                    existing.seller_claims_verified = True

        return unique_listings
