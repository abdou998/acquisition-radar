"""
Industry CPC (Cost Per Click) and RPM (Revenue Per Mille) benchmarks for valuation.
Calibrated against real-world Google Ads and display ad network rates (AdSense, Mediavine, Raptive).
"""

from typing import Dict, Any

NICHE_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "finance": {
        "name": "Finance, Investing & Fintech",
        "cpc_low": 1.80, "cpc_base": 3.50, "cpc_high": 7.50,
        "display_rpm_low": 20.0, "display_rpm_base": 38.0, "display_rpm_high": 65.0,
        "affiliate_conversion_pct": 2.5, "avg_affiliate_payout": 45.0,
        "default_commercial_intent": 0.55
    },
    "saas_b2b": {
        "name": "B2B, SaaS & Developer Tools",
        "cpc_low": 1.50, "cpc_base": 3.20, "cpc_high": 6.80,
        "display_rpm_low": 14.0, "display_rpm_base": 26.0, "display_rpm_high": 45.0,
        "affiliate_conversion_pct": 1.8, "avg_affiliate_payout": 35.0,
        "default_commercial_intent": 0.50
    },
    "tech_web": {
        "name": "Technology, Web Design & Coding",
        "cpc_low": 0.90, "cpc_base": 1.90, "cpc_high": 3.80,
        "display_rpm_low": 10.0, "display_rpm_base": 20.0, "display_rpm_high": 35.0,
        "affiliate_conversion_pct": 2.0, "avg_affiliate_payout": 25.0,
        "default_commercial_intent": 0.35
    },
    "health_wellness": {
        "name": "Health, Fitness & Wellness",
        "cpc_low": 0.80, "cpc_base": 1.80, "cpc_high": 4.00,
        "display_rpm_low": 12.0, "display_rpm_base": 24.0, "display_rpm_high": 42.0,
        "affiliate_conversion_pct": 2.8, "avg_affiliate_payout": 30.0,
        "default_commercial_intent": 0.40
    },
    "home_lifestyle": {
        "name": "Home, DIY, Pets & Lifestyle",
        "cpc_low": 0.45, "cpc_base": 1.10, "cpc_high": 2.20,
        "display_rpm_low": 11.0, "display_rpm_base": 22.0, "display_rpm_high": 36.0,
        "affiliate_conversion_pct": 3.2, "avg_affiliate_payout": 15.0,
        "default_commercial_intent": 0.35
    },
    "utilities_tools": {
        "name": "Utilities, Calculators & Online Tools",
        "cpc_low": 0.35, "cpc_base": 0.85, "cpc_high": 1.90,
        "display_rpm_low": 7.0, "display_rpm_base": 15.0, "display_rpm_high": 28.0,
        "affiliate_conversion_pct": 1.2, "avg_affiliate_payout": 18.0,
        "default_commercial_intent": 0.30
    },
    "education_career": {
        "name": "Education, Jobs & Career",
        "cpc_low": 0.75, "cpc_base": 1.70, "cpc_high": 3.60,
        "display_rpm_low": 10.0, "display_rpm_base": 19.0, "display_rpm_high": 32.0,
        "affiliate_conversion_pct": 2.0, "avg_affiliate_payout": 22.0,
        "default_commercial_intent": 0.40
    },
    "general": {
        "name": "General & Entertainment",
        "cpc_low": 0.20, "cpc_base": 0.50, "cpc_high": 1.10,
        "display_rpm_low": 4.0, "display_rpm_base": 9.0, "display_rpm_high": 18.0,
        "affiliate_conversion_pct": 1.0, "avg_affiliate_payout": 10.0,
        "default_commercial_intent": 0.20
    }
}

def get_niche_benchmark(category: str, title: str = "", description: str = "") -> Dict[str, Any]:
    text = f"{category} {title} {description}".lower()
    if any(k in text for k in ["crypto", "finance", "invest", "stock", "loan", "insurance", "credit", "banking"]):
        return NICHE_BENCHMARKS["finance"]
    if any(k in text for k in ["saas", "software", "api", "crm", "b2b", "developer", "chrome extension"]):
        return NICHE_BENCHMARKS["saas_b2b"]
    if any(k in text for k in ["tech", "coding", "web design", "programming", "hosting", "hardware"]):
        return NICHE_BENCHMARKS["tech_web"]
    if any(k in text for k in ["fitness", "health", "workout", "diet", "mental health", "wellness"]):
        return NICHE_BENCHMARKS["health_wellness"]
    if any(k in text for k in ["home", "garden", "diy", "pet", "dog", "cat", "decor", "recipe", "food"]):
        return NICHE_BENCHMARKS["home_lifestyle"]
    if any(k in text for k in ["calculator", "tool", "converter", "generator", "checker", "formatter"]):
        return NICHE_BENCHMARKS["utilities_tools"]
    if any(k in text for k in ["career", "resume", "job", "education", "course", "tutor", "learn"]):
        return NICHE_BENCHMARKS["education_career"]
    return NICHE_BENCHMARKS["general"]
