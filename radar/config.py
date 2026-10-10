"""
Configuration manager for the Daily Undervalued Online Business Acquisition Radar.
Loads environment variables and YAML/JSON configurations.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load .env file from project root if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class AcquisitionConfig:
    # Budget Settings
    max_normal_budget_usd: float = float(os.getenv("RADAR_MAX_NORMAL_BUDGET", "1000.0"))
    max_exceptional_budget_usd: float = float(os.getenv("RADAR_MAX_EXCEPTIONAL_BUDGET", "5000.0"))
    min_price_usd: float = float(os.getenv("RADAR_MIN_PRICE", "50.0"))

    # Scoring Weights (Total = 100)
    weight_audience: float = 25.0
    weight_seo: float = 20.0
    weight_financial: float = 20.0
    weight_price: float = 15.0
    weight_transfer: float = 10.0
    weight_risk: float = 10.0

    # Classification Thresholds
    shortlist_score_threshold: float = 70.0
    watchlist_score_threshold: float = 50.0

    # Operational Assumptions
    default_escrow_min_fee: float = 30.0
    default_escrow_rate: float = 0.0325  # 3.25% standard escrow
    default_domain_transfer_cost: float = 15.0
    default_max_weekly_hours: float = 10.0

    # Daily Schedule
    schedule_time: str = os.getenv("RADAR_SCHEDULE_TIME", "08:00")
    schedule_timezone: str = os.getenv("RADAR_TIMEZONE", "Africa/Casablanca")

    # Delivery Settings
    enable_email: bool = os.getenv("RADAR_ENABLE_EMAIL", "false").lower() in ("true", "1", "yes")
    smtp_host: str = os.getenv("RADAR_SMTP_HOST", "")
    smtp_port: int = int(os.getenv("RADAR_SMTP_PORT", "587"))
    smtp_user: str = os.getenv("RADAR_SMTP_USER", "")
    smtp_password: str = os.getenv("RADAR_SMTP_PASSWORD", "")
    smtp_sender: str = os.getenv("RADAR_SMTP_SENDER", "")
    email_recipient: str = os.getenv("RADAR_EMAIL_RECIPIENT", "")

    enable_telegram: bool = os.getenv("RADAR_ENABLE_TELEGRAM", "false").lower() in ("true", "1", "yes")
    telegram_bot_token: str = os.getenv("RADAR_TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("RADAR_TELEGRAM_CHAT_ID", "")

    # Storage Settings
    database_path: str = os.getenv("RADAR_DB_PATH", str(BASE_DIR / "radar.db"))
    reports_dir: str = os.getenv("RADAR_REPORTS_DIR", str(BASE_DIR / "reports"))

    # Marketplace API Keys (Optional)
    flippa_api_key: str = os.getenv("FLIPPA_API_KEY", "")
    acquire_api_key: str = os.getenv("ACQUIRE_API_KEY", "")

    # SEO & Research APIs (Optional, system uses smart open heuristics by default)
    serp_api_key: str = os.getenv("SERP_API_KEY", "")
    open_pagerank_key: str = os.getenv("OPEN_PAGERANK_KEY", "")

config = AcquisitionConfig()
