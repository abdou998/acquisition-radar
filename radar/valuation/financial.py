"""
Financial Due Diligence and Acquisition Cost Engine.
Calculates all-in transaction costs, multiples, payback period, and red flag warnings.
"""

from typing import Dict, Any, List, Tuple
from radar.models import Listing
from radar.config import config

class FinancialValuator:
    @staticmethod
    def calculate_all_in_cost(asking_price: float, source: str) -> Tuple[float, float, float]:
        """
        Calculates all-in acquisition cost including escrow, platform fees, and transfer costs.
        Returns: (total_cost, escrow_fee, transfer_fee)
        """
        if asking_price <= 0:
            return 0.0, 0.0, 0.0

        # Escrow.com or built-in escrow standard fee (min $30 or 3.25%)
        escrow_fee = max(config.default_escrow_min_fee, asking_price * config.default_escrow_rate)

        # Domain & asset transfer fees (e.g. registrar transfer fee ~$15)
        transfer_fee = config.default_domain_transfer_cost

        # Marketplace specific buyer fees
        platform_fee = 0.0
        if source.lower() == "flippa":
            # Flippa buyer success fee is typically ~5% (min $15)
            platform_fee = max(15.0, asking_price * 0.05)

        total_cost = round(asking_price + escrow_fee + transfer_fee + platform_fee, 2)
        return total_cost, round(escrow_fee + platform_fee, 2), round(transfer_fee, 2)

    @staticmethod
    def calculate_payback_periods(total_cost: float, claimed_profit: float, potential_base_rev: float) -> Tuple[float, float]:
        """
        Calculates conservative and base payback periods in months.
        Conservative uses 70% of claimed profit (or 40% of potential monetization if current profit is $0).
        Base uses 100% of claimed profit (or 80% of potential monetization).
        Returns: (conservative_months, base_months)
        """
        if total_cost <= 0:
            return 0.0, 0.0

        # Determine monthly cash flow baseline
        if claimed_profit > 0:
            cons_cash_flow = claimed_profit * 0.70
            base_cash_flow = claimed_profit * 1.0
        elif potential_base_rev > 0:
            cons_cash_flow = potential_base_rev * 0.35  # Assume conservative net margin
            base_cash_flow = potential_base_rev * 0.65
        else:
            return 99.0, 99.0

        cons_months = round(total_cost / cons_cash_flow, 1) if cons_cash_flow > 0 else 99.0
        base_months = round(total_cost / base_cash_flow, 1) if base_cash_flow > 0 else 99.0

        return cons_months, base_months

    @staticmethod
    def identify_red_flags(listing: Listing) -> List[str]:
        """
        Detects financial, operational, and traffic anomalies that require skepticism.
        """
        flags = []

        # 1. Revenue without traffic
        if listing.monthly_revenue > 100 and listing.monthly_visitors < 50 and listing.subscribers_count < 100:
            flags.append("Suspicious: High claimed revenue ($%d/mo) with virtually zero traffic (<50 visits). Request live payment dashboard." % int(listing.monthly_revenue))

        # 2. Extreme profit margins with complex operations
        if listing.monthly_revenue > 300 and (listing.monthly_profit / listing.monthly_revenue) > 0.98 and listing.category in ["E-commerce"]:
            flags.append("Implausible 98%+ net margin claimed for e-commerce. Audit COGS and ad spend.")

        # 3. High asking price relative to zero metrics
        if listing.asking_price > 1000 and listing.monthly_visitors < 100 and listing.monthly_revenue == 0:
            flags.append("Overpriced concept site: Seller asking $%d with negligible traffic and no monetization." % int(listing.asking_price))

        # 4. Unverifiable seller metrics
        if not listing.seller_claims_verified and listing.monthly_revenue > 200:
            flags.append("Unverified financial claims: No third-party platform integration (Stripe/PayPal/AdSense) attached to listing.")

        # 5. Personal brand dependency
        desc_lower = listing.description.lower()
        if any(p in desc_lower for p in ["my personal brand", "my name", "my clients", "my consulting"]):
            flags.append("Personal brand concentration: Asset may rely on seller's personal reputation and fail to transfer cleanly.")

        # 6. Fragile / scraping dependencies
        if any(t in desc_lower for t in ["scrapes", "unofficial api", "bypasses", "automation tool for instagram", "tiktok scraper"]):
            flags.append("Platform policy risk: Relies on scraping or unofficial APIs vulnerable to sudden blocking.")

        return flags

    @staticmethod
    def generate_diligence_checklist(listing: Listing) -> List[str]:
        """
        Creates a custom pre-purchase verification protocol.
        """
        checklist = [
            "Request read-only Google Search Console (GSC) and Google Analytics 4 (GA4) access for the past 12 months.",
            "Verify domain ownership via WHOIS / DNS TXT challenge before escrow initiation.",
            "Use Escrow.com or marketplace escrow with milestone release conditioned on successful code, domain, and asset transfer."
        ]

        if listing.monthly_revenue > 0:
            checklist.append("Inspect live video screen-share or direct read-only export of payment processor (Stripe/PayPal/Paddle/Lemon Squeezy) including refunds.")

        if listing.category in ["Micro-SaaS", "Tool/Utility"]:
            checklist.append("Review repository codebase (GitHub/GitLab), third-party dependencies, and monthly hosting/cloud API costs.")
            checklist.append("Confirm all external API keys, auth services (Supabase/Firebase/Auth0), and database access can be transferred cleanly.")
        elif listing.category == "Newsletter":
            checklist.append("Verify subscriber open rates (>30%), click rates, and historical bounce/unsub rates via ESP (Beehiiv/Substack/ConvertKit).")
        elif listing.category == "Content/Blog":
            checklist.append("Run full Copyscape plagiarism check to ensure articles are original and not scraped or low-effort AI spun text.")
            checklist.append("Verify affiliate link account ownership and ensure affiliate programs allow new owner re-assignment.")

        return checklist
