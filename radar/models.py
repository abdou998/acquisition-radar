"""
Domain models for the Acquisition Radar.
Defines clean dataclasses for Listings, SEO Metrics, Valuations, Scores, and Runs.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

@dataclass
class Listing:
    id: str
    source: str                          # flippa, motion_invest, little_exits, sideprojectors, microns, acquire
    external_id: str
    url: str
    title: str
    description: str
    category: str                        # Micro-SaaS, Content/Blog, Newsletter, Tool/Utility, E-commerce, Community, Directory, Other
    asking_price: float                  # In USD
    currency: str = "USD"
    original_price: Optional[float] = None
    monthly_revenue: float = 0.0
    monthly_profit: float = 0.0
    monthly_visitors: int = 0
    monthly_pageviews: int = 0
    monthly_search_clicks: int = 0
    subscribers_count: int = 0
    domain: Optional[str] = None
    domain_age_years: float = 0.0
    tech_stack: str = "Unknown"
    hours_per_week: float = 2.0
    monetization_methods: List[str] = field(default_factory=list)
    assets_included: List[str] = field(default_factory=list)
    seller_claims_verified: bool = False
    first_seen_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "active"               # active, price_reduced, sold, delisted, relisted
    price_change_amount: float = 0.0
    price_change_percent: float = 0.0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Listing":
        valid_keys = cls.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class SEOMetrics:
    listing_id: str
    domain: Optional[str] = None
    estimated_monthly_organic_visits: int = 0
    ranking_keywords_count: int = 0
    top_keywords: List[str] = field(default_factory=list)
    commercial_intent_ratio: float = 0.20   # 0.0 to 1.0
    backlinks_count: int = 0
    referring_domains: int = 0
    domain_authority_proxy: float = 10.0   # 0 to 100
    indexed_pages: int = 0
    brand_search_ratio: float = 0.10
    traffic_trend_6m: str = "stable"       # growing, stable, declining, spiking, unknown
    traffic_trend_change_pct: float = 0.0
    serp_competition_level: str = "medium" # low, medium, high
    ai_overview_vulnerability: str = "medium" # low, medium, high
    content_gap_opportunity: str = ""
    seo_health_notes: List[str] = field(default_factory=list)
    confidence: str = "low"                # verified, high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SEOMetrics":
        valid_keys = cls.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class Valuation:
    listing_id: str
    total_acquisition_cost: float = 0.0     # Price + escrow + transfer
    escrow_fee_estimate: float = 0.0
    transfer_fee_estimate: float = 0.0
    ad_equivalent_value_low: float = 0.0    # Advertising-equivalent monthly value
    ad_equivalent_value_base: float = 0.0
    ad_equivalent_value_high: float = 0.0
    monetization_potential_low: float = 0.0 # Realistic potential monthly revenue
    monetization_potential_base: float = 0.0
    monetization_potential_high: float = 0.0
    rebuild_cost_estimate: float = 0.0      # Replacement / rebuild cost
    rebuild_months_estimate: int = 6
    valuation_multiple: float = 0.0         # Price / (monthly_profit * 12) or ARR
    payback_period_months_conservative: float = 0.0
    payback_period_months_base: float = 0.0
    undervaluation_thesis: str = ""
    action_plan_30_days: List[str] = field(default_factory=list)
    estimated_improvement_cost: float = 0.0
    estimated_weekly_hours: float = 4.0
    due_diligence_checklist: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Valuation":
        valid_keys = cls.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class ScoreBreakdown:
    listing_id: str
    audience_score: float = 0.0   # max 25
    seo_score: float = 0.0        # max 20
    financial_score: float = 0.0  # max 20
    price_score: float = 0.0      # max 15
    transfer_score: float = 0.0   # max 10
    risk_score: float = 0.0       # max 10
    penalties: float = 0.0
    penalty_reasons: List[str] = field(default_factory=list)
    total_score: float = 0.0      # 0 to 100
    classification: str = "REJECTED"  # BUYER_SHORTLIST, WATCHLIST, REJECTED
    rejection_reasons: List[str] = field(default_factory=list)
    exceptional_5k_candidate: bool = False
    exceptional_justification: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoreBreakdown":
        valid_keys = cls.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class CompleteOpportunity:
    listing: Listing
    seo: SEOMetrics
    valuation: Valuation
    score: ScoreBreakdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing": self.listing.to_dict(),
            "seo": self.seo.to_dict(),
            "valuation": self.valuation.to_dict(),
            "score": self.score.to_dict()
        }


@dataclass
class DailyRun:
    run_id: str
    run_date: str
    total_discovered: int = 0
    new_listings_count: int = 0
    price_reductions_count: int = 0
    under_1k_count: int = 0
    shortlist_count: int = 0
    watchlist_count: int = 0
    rejected_count: int = 0
    exceptional_5k_count: int = 0
    most_interesting_deal_id: Optional[str] = None
    report_markdown_path: str = ""
    report_html_path: str = ""
    delivery_status: Dict[str, Any] = field(default_factory=dict)
    source_health: Dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
