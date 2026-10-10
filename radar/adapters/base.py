"""
Base class for Acquisition Marketplace Adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from radar.models import Listing

class BaseMarketplaceAdapter(ABC):
    name: str = "base"
    display_name: str = "Base Marketplace"
    base_url: str = ""
    is_enabled: bool = True

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    @abstractmethod
    async def fetch_listings(self) -> List[Listing]:
        """
        Fetches and normalizes listings from the marketplace.
        """
        pass

    @abstractmethod
    def get_access_method_doc(self) -> Dict[str, Any]:
        """
        Returns documentation on how this marketplace is accessed,
        including availability, legitimacy, buyer protection, and access constraints.
        """
        pass

    async def check_health(self) -> Dict[str, Any]:
        """
        Performs connectivity pre-flight check.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(self.base_url, headers=self.headers)
                return {
                    "source": self.name,
                    "status": "healthy" if resp.status_code in [200, 301, 302] else "degraded",
                    "status_code": resp.status_code,
                    "error": None
                }
        except Exception as e:
            return {
                "source": self.name,
                "status": "offline",
                "status_code": None,
                "error": str(e)
            }
