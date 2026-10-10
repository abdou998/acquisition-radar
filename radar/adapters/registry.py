"""
Marketplace Adapter Registry and Health Monitor.
Coordinates multi-source data ingestion, error isolation, and connectivity audits.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from radar.adapters.base import BaseMarketplaceAdapter
from radar.adapters.flippa import FlippaAdapter
from radar.adapters.motion_invest import MotionInvestAdapter
from radar.adapters.little_exits import LittleExitsAdapter
from radar.adapters.sideprojectors import SideProjectorsAdapter
from radar.adapters.microns import MicronsAdapter
from radar.adapters.acquire import AcquireAdapter
from radar.adapters.investors_club import InvestorsClubAdapter
from radar.models import Listing
from radar.core.deduplicator import Deduplicator

FIXTURES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "fixtures" / "verified_deals.json"

class AdapterRegistry:
    def __init__(self):
        self.adapters: Dict[str, BaseMarketplaceAdapter] = {
            "flippa": FlippaAdapter(),
            "motion_invest": MotionInvestAdapter(),
            "little_exits": LittleExitsAdapter(),
            "sideprojectors": SideProjectorsAdapter(),
            "microns": MicronsAdapter(),
            "acquire": AcquireAdapter(),
            "investors_club": InvestorsClubAdapter()
        }

    def get_adapter(self, name: str) -> Optional[BaseMarketplaceAdapter]:
        return self.adapters.get(name)

    def list_sources_documentation(self) -> List[Dict[str, Any]]:
        return [adapter.get_access_method_doc() for adapter in self.adapters.values()]

    async def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        tasks = [adapter.check_health() for adapter in self.adapters.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        health_report = {}
        for adapter, res in zip(self.adapters.values(), results):
            if isinstance(res, Exception):
                health_report[adapter.name] = {
                    "source": adapter.name,
                    "status": "error",
                    "error": str(res)
                }
            else:
                health_report[adapter.name] = res
        return health_report

    async def fetch_all(self, include_fixtures: bool = True) -> Tuple[List[Listing], Dict[str, Any]]:
        """
        Runs discovery cycle across all marketplace adapters concurrently.
        Returns: (deduplicated_listings, source_health_summary)
        """
        raw_listings: List[Listing] = []
        source_summary: Dict[str, Any] = {}

        tasks = [adapter.fetch_listings() for adapter in self.adapters.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for adapter, res in zip(self.adapters.values(), results):
            if isinstance(res, Exception):
                source_summary[adapter.name] = {
                    "status": "failed",
                    "count": 0,
                    "error": str(res)
                }
            else:
                count = len(res)
                source_summary[adapter.name] = {
                    "status": "success" if count > 0 else "idle",
                    "count": count,
                    "error": None
                }
                raw_listings.extend(res)

        # Include calibrated fixtures if available
        if include_fixtures and FIXTURES_PATH.exists():
            try:
                with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        raw_listings.append(Listing.from_dict(item))
                source_summary["curated_radar_feed"] = {
                    "status": "success",
                    "count": len(data),
                    "note": "Calibrated acquisition opportunities across micro-SaaS, tools, content sites, and newsletters."
                }
            except Exception as e:
                source_summary["curated_radar_feed"] = {
                    "status": "error",
                    "error": str(e)
                }

        # Cross-marketplace deduplication
        deduped = Deduplicator.deduplicate_batch(raw_listings)

        return deduped, source_summary

registry = AdapterRegistry()
