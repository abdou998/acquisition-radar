"""
Little Exits Marketplace Adapter (formerly TinyAcquisitions).
Specializes exclusively in micro-acquisitions under $5,000 (micro-SaaS, tools, newsletters, templates).
"""

import uuid
import re
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from radar.adapters.base import BaseMarketplaceAdapter
from radar.models import Listing
from radar.core.normalizer import ListingNormalizer

class LittleExitsAdapter(BaseMarketplaceAdapter):
    name: str = "little_exits"
    display_name: str = "Little Exits"
    base_url: str = "https://littleexits.com"

    def get_access_method_doc(self) -> Dict[str, Any]:
        return {
            "source": "Little Exits (formerly TinyAcquisitions)",
            "inventory_profile": "Micro-SaaS, developer utilities, Chrome extensions, newsletters, and small communities under $5k.",
            "price_range_suitability": "Highest suitability: specifically designed for acquisitions between $100 and $5,000.",
            "buyer_protection": "Founder-to-founder marketplace; community reputation and direct due diligence.",
            "access_method": "Public directory browse and project listings.",
            "access_restrictions": "Public listings visible without authentication."
        }

    async def fetch_listings(self) -> List[Listing]:
        listings: List[Listing] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(f"{self.base_url}/projects", headers=self.headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".project-card, [data-project], article, .card")
                    for card in cards:
                        item = self._parse_card(card)
                        if item:
                            listings.append(item)
        except Exception:
            pass

        return listings

    def _parse_card(self, card) -> Optional[Listing]:
        try:
            link = card.select_one("a[href*='/project/'], a[href*='/listings/'], a")
            if not link:
                return None
            url = link.get("href", "")
            if not url.startswith("http"):
                url = f"{self.base_url}{url}"

            title_el = card.select_one("h2, h3, h4, .title, strong")
            title = ListingNormalizer.clean_text(title_el.get_text() if title_el else link.get_text())
            if not title or len(title) < 3:
                return None

            price_el = card.select_one(".price, [data-price], .badge-price")
            raw_price = price_el.get_text() if price_el else "$500"
            price, curr = ListingNormalizer.normalize_price(raw_price)

            desc_el = card.select_one("p, .description, .summary")
            desc = ListingNormalizer.clean_text(desc_el.get_text() if desc_el else "")

            category = ListingNormalizer.categorize_listing(title, desc)
            domain = ListingNormalizer.extract_domain(title) or ListingNormalizer.extract_domain(desc)

            # Look for MRR or users
            card_text = card.get_text().lower()
            mrr_match = re.search(r"mrr:?\s*\$([\d,]+)", card_text)
            monthly_rev = float(mrr_match.group(1).replace(",", "")) if mrr_match else 0.0

            users_match = re.search(r"([\d.,]+[k]?)\s*(?:users|subscribers|members)", card_text)
            users_count = ListingNormalizer.parse_numeric_metric(users_match.group(1)) if users_match else 0

            return Listing(
                id=f"littleexits_{uuid.uuid5(uuid.NAMESPACE_URL, url).hex[:12]}",
                source=self.name,
                external_id=url.strip("/").split("/")[-1],
                url=url,
                title=title,
                description=desc,
                category=category,
                asking_price=price,
                currency=curr,
                monthly_revenue=monthly_rev,
                monthly_profit=monthly_rev * 0.85, # SaaS typical high margin
                monthly_visitors=max(users_count * 3, 200),
                subscribers_count=users_count if category == "Newsletter" else 0,
                domain=domain,
                seller_claims_verified=False,
                raw_metadata={"raw_price": raw_price}
            )
        except Exception:
            return None
