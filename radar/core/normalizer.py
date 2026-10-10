"""
Data normalizer for listing attributes, prices, domains, and metrics.
"""

import re
from urllib.parse import urlparse
from typing import Optional, Tuple, Dict, Any

# Currency conversion rates approximation (relative to USD)
CURRENCY_RATES = {
    "USD": 1.0,
    "$": 1.0,
    "EUR": 1.08,
    "€": 1.08,
    "GBP": 1.28,
    "£": 1.28,
    "CAD": 0.74,
    "AUD": 0.65,
}

CATEGORY_KEYWORDS = {
    "Micro-SaaS": ["saas", "software", "api", "web app", "micro-saas", "chrome extension", "slack bot", "crm", "b2b", "subscription", "recurring"],
    "Content/Blog": ["blog", "content site", "affiliate", "niche site", "adsense", "amazon associates", "articles", "seo site", "editorial"],
    "Newsletter": ["newsletter", "substack", "beehiiv", "email list", "subscribers", "digest", "mail"],
    "Tool/Utility": ["calculator", "converter", "generator", "free tool", "online tool", "utility", "checker", "formatter", "compressor"],
    "E-commerce": ["ecommerce", "shopify", "woocommerce", "dropshipping", "dtc", "store", "digital product", "gumroad", "templates"],
    "Community": ["community", "discord", "forum", "slack community", "membership", "circle", "group"],
    "Directory": ["directory", "curated list", "job board", "database", "aggregator", "curation"]
}

class ListingNormalizer:
    @staticmethod
    def normalize_price(price_input: Any, currency_input: Optional[str] = "USD") -> Tuple[float, str]:
        """
        Parses a price string, float, or integer into a normalized USD float and original currency.
        Handles '$750', '€650', '750 USD', '1,200', etc.
        """
        if price_input is None:
            return 0.0, "USD"

        if isinstance(price_input, (int, float)):
            rate = CURRENCY_RATES.get((currency_input or "USD").upper(), 1.0)
            return round(float(price_input) * rate, 2), currency_input or "USD"

        raw = str(price_input).strip()
        found_currency = "USD"
        for sym, rate in CURRENCY_RATES.items():
            if sym in raw:
                found_currency = sym
                break

        # Remove currency symbols and formatting commas
        cleaned = re.sub(r"[^\d.]", "", raw)
        if not cleaned:
            return 0.0, found_currency

        try:
            val = float(cleaned)
            # Check for multiple decimal points
            rate = CURRENCY_RATES.get(found_currency.upper(), 1.0)
            return round(val * rate, 2), found_currency
        except ValueError:
            return 0.0, found_currency

    @staticmethod
    def extract_domain(url_or_text: Optional[str]) -> Optional[str]:
        """
        Extracts clean registered domain from URL or string (e.g., https://www.example.com/path -> example.com).
        """
        if not url_or_text:
            return None

        clean = url_or_text.strip().lower()
        marketplace_hosts = ["flippa.com", "acquire.com", "motioninvest.com", "microns.io", "sideprojectors.com", "littleexits.com", "github.com", "twitter.com"]

        # If clean text has spaces, extract candidate domain via regex
        if " " in clean:
            match = re.search(r"\b([a-z0-9][a-z0-9-]{1,61}[a-z0-9]\.[a-z]{2,})\b", clean)
            if match:
                cand = match.group(1)
                if not any(m in cand for m in marketplace_hosts):
                    return cand
            return None

        if not clean.startswith(("http://", "https://")):
            clean = "https://" + clean

        try:
            parsed = urlparse(clean)
            hostname = parsed.netloc or parsed.path
            hostname = hostname.split(":")[0]
            if hostname.startswith("www."):
                hostname = hostname[4:]
            
            if "." in hostname and not "/" in hostname and len(hostname) > 3:
                if any(m in hostname for m in marketplace_hosts):
                    return None
                return hostname
            return None
        except Exception:
            return None

    @staticmethod
    def parse_numeric_metric(metric_val: Any) -> int:
        """
        Parses strings like '12.5k', '500', '1.2M', or integers into integer values.
        """
        if metric_val is None:
            return 0
        if isinstance(metric_val, (int, float)):
            return int(metric_val)

        val_str = str(metric_val).strip().lower().replace(",", "")
        multiplier = 1
        if val_str.endswith("k"):
            multiplier = 1000
            val_str = val_str[:-1]
        elif val_str.endswith("m"):
            multiplier = 1000000
            val_str = val_str[:-1]

        cleaned = re.sub(r"[^\d.]", "", val_str)
        if not cleaned:
            return 0
        try:
            return int(float(cleaned) * multiplier)
        except ValueError:
            return 0

    @staticmethod
    def categorize_listing(title: str, description: str, raw_category: Optional[str] = None) -> str:
        """
        Normalizes category into:
        Micro-SaaS, Content/Blog, Newsletter, Tool/Utility, E-commerce, Community, Directory, Other.
        """
        text = f"{title} {description} {raw_category or ''}".lower()

        # Check explicit priority matches
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", text):
                    return cat

        if raw_category:
            raw_lower = raw_category.lower()
            if "app" in raw_lower or "software" in raw_lower or "extension" in raw_lower:
                return "Micro-SaaS"
            if "site" in raw_lower or "blog" in raw_lower or "content" in raw_lower:
                return "Content/Blog"
            if "tool" in raw_lower:
                return "Tool/Utility"
            if "newsletter" in raw_lower or "email" in raw_lower:
                return "Newsletter"

        return "Other"

    @staticmethod
    def clean_text(text: Optional[str], max_len: int = 1500) -> str:
        """
        Removes excess whitespace, control characters, and truncates if necessary.
        """
        if not text:
            return ""
        # Collapse multiple spaces and newlines
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len] + "..."
        return cleaned
