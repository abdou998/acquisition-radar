"""
Flippa Marketplace Adapter.
Fetches website, micro-SaaS, and digital asset listings from Flippa.
Supports multi-page catalog discovery across classifieds and auctions,
detail-level Buy It Now & reserve verification, and official API integration.
"""

import asyncio
import re
import uuid
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
            "access_method": "Multi-page public search discovery and classifieds parsing; supports official API if FLIPPA_API_KEY configured.",
            "access_restrictions": "Cloudflare bot detection on direct headless requests. Compliant user-agent and rate limit applied."
        }

    async def fetch_listings(self) -> List[Listing]:
        if config.flippa_api_key:
            return await self._fetch_via_api()

        listings: List[Listing] = []
        seen_urls = set()

        # Broad discovery endpoints covering classifieds (guaranteed fixed price) and open listings
        endpoints = [
            # Classifieds (fixed price, zero bidding games or hidden reserves)
            f"{self.base_url}/search?filter[property_type]=website&filter[sale_method]=classified&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            f"{self.base_url}/search?filter[property_type]=website&filter[sale_method]=classified&filter[price][max]={int(config.max_normal_budget_usd)}&page=2",
            f"{self.base_url}/search?filter[property_type]=saas&filter[sale_method]=classified&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            f"{self.base_url}/search?filter[property_type]=ecommerce&filter[sale_method]=classified&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            f"{self.base_url}/search?filter[property_type]=app&filter[sale_method]=classified&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            # Open search (recent additions & general search)
            f"{self.base_url}/search?filter[property_type]=website&filter[status]=open&filter[price][max]={int(config.max_normal_budget_usd)}&sort=most_recent",
            f"{self.base_url}/search?filter[property_type]=website&filter[status]=open&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            f"{self.base_url}/search?filter[property_type]=website&filter[status]=open&filter[price][max]={int(config.max_normal_budget_usd)}&page=2",
            f"{self.base_url}/search?filter[property_type]=saas&filter[status]=open&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            f"{self.base_url}/search?filter[property_type]=ecommerce&filter[status]=open&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            f"{self.base_url}/search?filter[property_type]=app&filter[status]=open&filter[price][max]={int(config.max_normal_budget_usd)}&page=1",
            # Exceptional candidates up to $5,000
            f"{self.base_url}/search?filter[property_type]=website&filter[status]=open&filter[price][max]={int(config.max_exceptional_budget_usd)}&sort=most_recent"
        ]

        candidate_listings: List[Listing] = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                for ep in endpoints:
                    try:
                        resp = await client.get(ep, headers=self.headers)
                        if resp.status_code != 200:
                            continue
                        soup = BeautifulSoup(resp.text, "html.parser")
                        links = soup.find_all("a", href=lambda h: h and re.search(r"/\d{7,8}-", h))
                        for a in links:
                            href = a.get("href", "").split("?")[0]
                            if not href or href in seen_urls:
                                continue
                            seen_urls.add(href)
                            item = self._parse_flippa_anchor(a)
                            if item:
                                candidate_listings.append(item)
                    except Exception:
                        continue

                # Concurrently audit candidate auctions to verify true Buy It Now and reserve status
                sem = asyncio.Semaphore(5)
                async def _audit_safe(item: Listing):
                    async with sem:
                        await self._audit_listing_detail(client, item)

                # Target auctions with bids under budget that might have hidden reserves / high BINs
                auctions_to_audit = [
                    item for item in candidate_listings
                    if item.raw_metadata.get("sale_type") == "auction" and item.asking_price <= config.max_normal_budget_usd
                ]
                audit_targets = auctions_to_audit[:15]
                if audit_targets:
                    await asyncio.gather(*(_audit_safe(item) for item in audit_targets), return_exceptions=True)

                listings = candidate_listings

        except Exception:
            pass

        return listings

    def _parse_flippa_anchor(self, a) -> Optional[Listing]:
        try:
            href = a.get("href", "")
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            
            # Walk up to find card container
            card = a
            for _ in range(8):
                if card.parent:
                    card = card.parent
                    classes = " ".join(card.get("class", []))
                    if "border" in classes and "@container" in classes:
                        break

            text = card.get_text(separator=" | ", strip=True)
            is_data_verified = "Data Verified" in text or "Verified Listing" in text

            # Precise price extraction distinguishing classified vs auction vs buy it now
            asking_match = re.search(r"Asking price\s*\|\s*USD\s*\$([\d,]+)", text, re.IGNORECASE)
            bin_card_match = re.search(r"Buy It Now\s*\|\s*USD\s*\$([\d,]+)", text, re.IGNORECASE)
            auction_match = re.search(r"Auction\s*\|\s*USD\s*\$([\d,]+)", text, re.IGNORECASE)
            bid_match = re.search(r"USD\s*\$([\d,]+)\s*\|\s*\d+\s*bids", text, re.IGNORECASE)

            current_bid = None
            if asking_match:
                price = float(asking_match.group(1).replace(",", ""))
                sale_type = "classified"
            elif bin_card_match:
                price = float(bin_card_match.group(1).replace(",", ""))
                sale_type = "buy_it_now"
            elif auction_match:
                price = float(auction_match.group(1).replace(",", ""))
                sale_type = "auction"
                current_bid = price
            elif bid_match:
                price = float(bid_match.group(1).replace(",", ""))
                sale_type = "auction"
                current_bid = price
            else:
                any_price = re.search(r"USD\s*\$([\d,]+)", text, re.IGNORECASE)
                price = float(any_price.group(1).replace(",", "")) if any_price else 500.0
                sale_type = "classified" if "asking price" in text.lower() else "unknown"

            # Check for price reduction
            red_match = re.search(r"USD\s*\$([\d,]+)\s*\|\s*USD\s*\$([\d,]+)\s*\|\s*Reduced\s*(\d+)%", text, re.IGNORECASE)
            orig_price = float(red_match.group(2).replace(",", "")) if red_match else price
            price_change_pct = -float(red_match.group(3)) if red_match else 0.0

            # Revenue extraction with K/M multiplier support
            rev_match = re.search(r"Monthly Revenue\s*\|\s*USD\s*\$([\d\.,]+[KkMm]?)", text, re.IGNORECASE)
            monthly_revenue = 0.0
            if rev_match:
                val_str = rev_match.group(1).replace(",", "")
                if val_str.lower().endswith("k"):
                    monthly_revenue = float(val_str[:-1]) * 1000.0
                elif val_str.lower().endswith("m"):
                    monthly_revenue = float(val_str[:-1]) * 1000000.0
                else:
                    monthly_revenue = float(val_str)

            # Profit extraction with K/M multiplier support
            profit_match = re.search(r"Monthly Profit\s*\|\s*USD\s*\$([\d\.,]+[KkMm]?)", text, re.IGNORECASE)
            monthly_profit = 0.0
            if profit_match:
                val_str = profit_match.group(1).replace(",", "")
                if val_str.lower().endswith("k"):
                    monthly_profit = float(val_str[:-1]) * 1000.0
                elif val_str.lower().endswith("m"):
                    monthly_profit = float(val_str[:-1]) * 1000000.0
                else:
                    monthly_profit = float(val_str)

            # Title
            title = ListingNormalizer.clean_text(a.get_text(strip=True))
            if not title or title.lower() in ["view listing", "watch", "bid now"]:
                h_el = card.find("h3") or card.find("h2") or card.find("strong")
                title = ListingNormalizer.clean_text(h_el.get_text(strip=True)) if h_el else "Flippa Digital Asset"

            desc = text[:250]
            domain = ListingNormalizer.extract_domain(title) or ListingNormalizer.extract_domain(desc) or ListingNormalizer.extract_domain(url)
            category = ListingNormalizer.categorize_listing(title, desc)

            est_visitors = max(int(monthly_revenue * 20), 400) if monthly_revenue > 0 else 250
            status = "price_reduced" if price_change_pct < 0 else "active"

            return Listing(
                id=f"flippa_{uuid.uuid5(uuid.NAMESPACE_URL, url).hex[:12]}",
                source=self.name,
                external_id=url.split("/")[-1].split("?")[0],
                url=url,
                title=title,
                description=desc,
                category=category,
                asking_price=price,
                original_price=orig_price,
                currency="USD",
                monthly_revenue=monthly_revenue,
                monthly_profit=monthly_profit,
                monthly_visitors=est_visitors,
                domain=domain,
                seller_claims_verified=is_data_verified,
                status=status,
                price_change_percent=price_change_pct,
                raw_metadata={
                    "data_verified": is_data_verified,
                    "sale_type": sale_type,
                    "current_bid": current_bid,
                    "card_snippet": text[:140]
                }
            )
        except Exception:
            return None

    async def _audit_listing_detail(self, client: httpx.AsyncClient, listing: Listing) -> None:
        """Audits the listing detail page to resolve true Buy It Now and reserve status."""
        try:
            resp = await client.get(listing.url, headers=self.headers, timeout=8.0)
            if resp.status_code != 200:
                return
            html = resp.text

            # 1. Check for Buy It Now
            bin_m = (
                re.search(r"Buy\s+It\s+Now(?:\s+for)?\s*(?:USD|\$)?\s*\$?([\d,]+)", html, re.IGNORECASE)
                or re.search(r"Buy\s+It\s+Now\s*\|\s*USD\s*\$([\d,]+)", html, re.IGNORECASE)
            )
            if bin_m:
                bin_price = float(bin_m.group(1).replace(",", ""))
                listing.raw_metadata["buy_it_now_price"] = bin_price
                # If auction displayed a low current bid, the real acquisition price is the Buy It Now price
                if listing.raw_metadata.get("sale_type") == "auction":
                    listing.asking_price = bin_price

            # 2. Check Reserve status
            reserve_not_met = "Reserve not met" in html
            reserve_met = "Reserve met" in html
            no_reserve = "No reserve" in html

            listing.raw_metadata["reserve_not_met"] = reserve_not_met
            listing.raw_metadata["reserve_met"] = reserve_met
            listing.raw_metadata["no_reserve"] = no_reserve

            if reserve_not_met:
                bin_p = listing.raw_metadata.get("buy_it_now_price")
                if bin_p:
                    listing.asking_price = bin_p
                else:
                    # Unmet reserve with no Buy It Now: cannot be acquired for the bid
                    listing.asking_price = 999999.0
                listing.raw_metadata["is_unmet_reserve_auction"] = True

            # 3. Check Google Analytics / AdSense badges
            if "Google Analytics" in html and ("Verified" in html or "Connected" in html):
                listing.seller_claims_verified = True
                listing.raw_metadata["google_analytics_verified"] = True

        except Exception:
            pass

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
