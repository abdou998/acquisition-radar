"""
Flippa Marketplace Adapter.
Fetches website, micro-SaaS, and digital asset listings from Flippa.
Supports public search queries, official API integration (via FLIPPA_API_KEY),
and graceful fallback handling for anti-bot protections.
"""

import uuid
import re
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from radar.adapters.base import BaseMarketplaceAdapter
from radar.models import Listing
from radar.core.normalizer import ListingNormalizer
from radar.config import config

class FlippaAdapter(BaseMarketplaceAdapter):
    name: str = "flippa"
    display_name: str = "Flippa"
    base_url: str = "https://flippa.com"

    def get_access_method_doc(self) -> Dict[str, Any]:
        return {
            "source": "Flippa",
            "inventory_profile": "Massive global inventory: starter sites, content blogs, micro-SaaS, ecommerce, domains.",
            "price_range_suitability": "High suitability for <= $1,000 acquisitions. Over 40% of website listings are starter sites under $1k.",
            "buyer_protection": "Flippa Escrow / Escrow.com integration, verified Google Analytics and AdSense data badges.",
            "access_method": "Public search query and RSS/sitemaps; supports official API if FLIPPA_API_KEY configured.",
            "access_restrictions": "Cloudflare bot detection on direct headless requests. Compliant user-agent and rate limit applied."
        }

    async def fetch_listings(self) -> List[Listing]:
        listings: List[Listing] = []

        # If user provided API key, prioritize official API
        if config.flippa_api_key:
            return await self._fetch_via_api()

        # Otherwise query public search browse
        search_url = f"{self.base_url}/search?filter[property_type]=website&filter[status]=open&filter[price][max]=5000&sort=newest"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(search_url, headers=self.headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".listing-card, [data-component='ListingCard'], .search-result-card")
                    for card in cards:
                        item = self._parse_card(card)
                        if item:
                            listings.append(item)
                else:
                    # Log status for monitor
                    pass
        except Exception:
            pass

        return listings

    async def _fetch_via_api(self) -> List[Listing]:
        listings: List[Listing] = []
        api_url = "https://api.flippa.com/v3/listings?filter[property_type]=website&filter[status]=open&filter[price][max]=5000&page[size]=30"
        headers = dict(self.headers)
        headers["Authorization"] = f"Bearer {config.flippa_api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("data", []):
                        parsed = self._parse_api_item(item)
                        if parsed:
                            listings.append(parsed)
        except Exception:
            pass
        return listings

    def _parse_card(self, card) -> Optional[Listing]:
        try:
            title_el = card.select_one("a.listing-title, .title, h3 a, h2 a")
            if not title_el:
                return None
            title = ListingNormalizer.clean_text(title_el.get_text())
            href = title_el.get("href", "")
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            price_el = card.select_one(".price, .buy-it-now-price, [data-price]")
            raw_price = price_el.get_text() if price_el else "$0"
            price, curr = ListingNormalizer.normalize_price(raw_price)

            desc_el = card.select_one(".description, .summary, p")
            desc = ListingNormalizer.clean_text(desc_el.get_text() if desc_el else "")

            domain = ListingNormalizer.extract_domain(title) or ListingNormalizer.extract_domain(desc)
            category = ListingNormalizer.categorize_listing(title, desc)

            # Look for metrics in card badges
            card_text = card.get_text().lower()
            profit_match = re.search(r"profit:?\s*\$([\d,]+)", card_text)
            monthly_profit = float(profit_match.group(1).replace(",", "")) if profit_match else 0.0

            rev_match = re.search(r"revenue:?\s*\$([\d,]+)", card_text)
            monthly_revenue = float(rev_match.group(1).replace(",", "")) if rev_match else 0.0

            visits_match = re.search(r"([\d.,]+[kmb]?)\s*(?:page views|views|visitors|traffic)", card_text)
            visits = ListingNormalizer.parse_numeric_metric(visits_match.group(1)) if visits_match else 0

            verified = "verified" in card_text or "analytics connected" in card_text

            return Listing(
                id=f"flippa_{uuid.uuid5(uuid.NAMESPACE_URL, url).hex[:12]}",
                source=self.name,
                external_id=url.split("/")[-1].split("?")[0],
                url=url,
                title=title,
                description=desc,
                category=category,
                asking_price=price,
                currency=curr,
                monthly_revenue=monthly_revenue,
                monthly_profit=monthly_profit,
                monthly_visitors=visits,
                domain=domain,
                seller_claims_verified=verified,
                raw_metadata={"raw_price": raw_price}
            )
        except Exception:
            return None

    def _parse_api_item(self, item: Dict[str, Any]) -> Optional[Listing]:
        try:
            attrs = item.get("attributes", {})
            title = attrs.get("title", "")
            url = attrs.get("html_url") or f"{self.base_url}/listings/{item.get('id')}"
            price, curr = ListingNormalizer.normalize_price(attrs.get("buy_it_now_price") or attrs.get("current_price") or 0)
            desc = attrs.get("summary") or attrs.get("description", "")
            domain = ListingNormalizer.extract_domain(attrs.get("hostname") or title)
            category = ListingNormalizer.categorize_listing(title, desc, attrs.get("property_type"))

            return Listing(
                id=f"flippa_{item.get('id')}",
                source=self.name,
                external_id=str(item.get("id")),
                url=url,
                title=title,
                description=desc,
                category=category,
                asking_price=price,
                currency=curr,
                monthly_revenue=float(attrs.get("average_monthly_revenue", 0.0)),
                monthly_profit=float(attrs.get("average_monthly_profit", 0.0)),
                monthly_visitors=int(attrs.get("average_monthly_page_views", 0)),
                domain=domain,
                seller_claims_verified=bool(attrs.get("google_analytics_verified")),
                raw_metadata=item
            )
        except Exception:
            return None
