"""
SideProjectors Marketplace Adapter.
Fetches listings from SideProjectors.com (side projects, micro-SaaS, tools, and starter sites).
"""

import uuid
import re
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from radar.adapters.base import BaseMarketplaceAdapter
from radar.models import Listing
from radar.core.normalizer import ListingNormalizer

class SideProjectorsAdapter(BaseMarketplaceAdapter):
    name: str = "sideprojectors"
    display_name: str = "SideProjectors"
    base_url: str = "https://www.sideprojectors.com"

    def get_access_method_doc(self) -> Dict[str, Any]:
        return {
            "source": "SideProjectors",
            "inventory_profile": "Side projects, micro-SaaS, tools, mobile apps, and domain concepts built by indie developers.",
            "price_range_suitability": "High: huge concentration of projects priced between $100 and $1,500.",
            "buyer_protection": "Peer-to-peer; no built-in escrow. Buyer must independently verify metrics and utilize Escrow.com.",
            "access_method": "Public explore/search directory.",
            "access_restrictions": "Publicly accessible pages."
        }

    async def fetch_listings(self) -> List[Listing]:
        listings: List[Listing] = []
        explore_url = f"{self.base_url}/project/explore"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(explore_url, headers=self.headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".project-item, .project-card, [data-project-id], .card")
                    for card in cards:
                        item = self._parse_card(card)
                        if item:
                            listings.append(item)
        except Exception:
            pass

        return listings

    def _parse_card(self, card) -> Optional[Listing]:
        try:
            link = card.select_one("a[href*='/project/']")
            if not link:
                return None
            url = link.get("href", "")
            if not url.startswith("http"):
                url = f"{self.base_url}{url}"

            title_el = card.select_one("h3, h4, .title, strong")
            title = ListingNormalizer.clean_text(title_el.get_text() if title_el else link.get_text())
            if not title or len(title) < 3:
                return None

            price_el = card.select_one(".price, .badge, [data-price]")
            raw_price = price_el.get_text() if price_el else "$300"
            price, curr = ListingNormalizer.normalize_price(raw_price)

            desc_el = card.select_one(".description, p, .summary")
            desc = ListingNormalizer.clean_text(desc_el.get_text() if desc_el else "")

            domain = ListingNormalizer.extract_domain(title) or ListingNormalizer.extract_domain(desc)
            category = ListingNormalizer.categorize_listing(title, desc)

            return Listing(
                id=f"sideproj_{uuid.uuid5(uuid.NAMESPACE_URL, url).hex[:12]}",
                source=self.name,
                external_id=url.strip("/").split("/")[-1],
                url=url,
                title=title,
                description=desc,
                category=category,
                asking_price=price,
                currency=curr,
                monthly_revenue=0.0,
                monthly_profit=0.0,
                monthly_visitors=150,
                domain=domain,
                seller_claims_verified=False,
                raw_metadata={"raw_price": raw_price}
            )
        except Exception:
            return None
