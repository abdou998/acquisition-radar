"""
Command Line Interface for the Acquisition Radar.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from radar.config import config
from radar.scheduler.runner import AcquisitionRadarRunner
from radar.database import db
from radar.adapters.registry import registry
from radar.ui.server import start_ui_server

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def cmd_run(args):
    """Executes live discovery and valuation cycle."""
    print("==================================================")
    print("   DAILY ACQUISITION RADAR -- DISCOVERY CYCLE     ")
    print("==================================================")
    run = asyncio.run(AcquisitionRadarRunner.run_discovery_cycle(include_fixtures=not args.live_only))
    print(f"\n[OK] Finished! Report saved to:\n    {run.report_markdown_path}\n    {run.report_html_path}")

def cmd_shortlist(args):
    """Prints current buyer shortlist under $1,000."""
    opportunities = db.get_all_complete_opportunities(
        classification="BUYER_SHORTLIST",
        max_price=config.max_normal_budget_usd
    )

    print("\n" + "="*80)
    print("       BUYER SHORTLIST — BEST ACQUISITIONS UNDER $1,000 USD")
    print("="*80)

    if not opportunities:
        print("\n  No active candidates on Buyer Shortlist. Run 'python -m radar.cli run' to scan.")
        print("="*80 + "\n")
        return

    for idx, opp in enumerate(opportunities, 1):
        l = opp.listing
        s = opp.score
        v = opp.valuation
        seo = opp.seo
        print(f"\n#{idx}. [{s.total_score}/100] {l.title}")
        print(f"    • Price: ${l.asking_price:,.0f} USD (All-in: ~${v.total_acquisition_cost:,.0f}) | Source: {l.source.title()}")
        print(f"    • Niche: {l.category} | Domain: {l.domain or 'Masked'} ({l.domain_age_years:.1f} yrs)")
        print(f"    • Traffic: {l.monthly_visitors:,} visits/mo | Search clicks: {seo.estimated_monthly_organic_visits:,}")
        print(f"    • Ad-Equivalent Traffic Value: ${v.ad_equivalent_value_base:,.0f}/mo | Rebuild Cost: ${v.rebuild_cost_estimate:,.0f}")
        print(f"    • Claimed Cash Flow: ${l.monthly_profit:,.0f}/mo | Est. Payback: {v.payback_period_months_conservative:.1f} months")
        print(f"    • Undervaluation Thesis: {v.undervaluation_thesis[:200]}...")
        print(f"    • Link: {l.url}")
    print("\n" + "="*80 + "\n")

def cmd_exceptional(args):
    """Prints exceptional candidates up to $5,000."""
    opportunities = db.get_all_complete_opportunities()
    exceptional = [o for o in opportunities if o.score.exceptional_5k_candidate]

    print("\n" + "="*80)
    print("   EXCEPTIONAL CANDIDATES UP TO $5,000 (HIGH-CONVICTION MOATS)")
    print("="*80)

    if not exceptional:
        print("\n  \"No exceptional opportunities justified exceeding the $1,000 budget today.\"")
        print("="*80 + "\n")
        return

    for opp in exceptional:
        l = opp.listing
        s = opp.score
        v = opp.valuation
        just = s.exceptional_justification
        print(f"\n[EXCEPTIONAL] [{s.total_score}/100] {l.title}")
        print(f"    • Asking Price: ${l.asking_price:,.0f} USD | Net Profit: ${l.monthly_profit:,.0f}/mo")
        print(f"    • Proven Payback: {v.payback_period_months_base:.1f} months | ARR: ${l.monthly_revenue * 12:,.0f}")
        print(f"    • Why Exceed Budget: {just.get('reason_to_exceed_budget')}")
        print(f"    • Link: {l.url}")
    print("\n" + "="*80 + "\n")

def cmd_sources(args):
    """Inspects and audits all marketplace adapters."""
    print("\n" + "="*80)
    print("       MARKETPLACE ADAPTERS & SOURCE INTEGRITY AUDIT")
    print("="*80 + "\n")

    docs = registry.list_sources_documentation()
    health = asyncio.run(registry.check_all_health())

    for doc in docs:
        name_key = doc["source"].lower().replace(".io", "").replace(".com", "").replace(" ", "_")
        if "tinyacquisitions" in name_key or "little" in name_key:
            name_key = "little_exits"
        h = health.get(name_key, {"status": "unknown"})

        status_icon = "🟢" if h.get("status") == "healthy" else ("🟡" if h.get("status") == "degraded" else "⚪")
        print(f"{status_icon} {doc['source']}")
        print(f"   • Inventory: {doc['inventory_profile']}")
        print(f"   • $1,000 Budget Fit: {doc['price_range_suitability']}")
        print(f"   • Buyer Protection: {doc['buyer_protection']}")
        print(f"   • Access Method: {doc['access_method']}")
        print(f"   • Constraints/Terms: {doc['access_restrictions']}")
        print(f"   • Live Connectivity: {h.get('status', 'unknown').upper()} (HTTP {h.get('status_code', 'N/A')})\n")

    print("="*80 + "\n")

def cmd_serve(args):
    """Launches interactive browser dashboard."""
    start_ui_server(host=args.host, port=args.port)

def cmd_daemon(args):
    """Starts background scheduled daemon."""
    AcquisitionRadarRunner.run_scheduled_daemon()

def main():
    parser = argparse.ArgumentParser(description="Daily Undervalued Online Business Acquisition Radar")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # run command
    p_run = subparsers.add_parser("run", help="Run full discovery and valuation cycle now")
    p_run.add_argument("--live-only", action="store_true", help="Only query live external endpoints without fixtures")
    p_run.set_defaults(func=cmd_run)

    # shortlist command
    p_short = subparsers.add_parser("shortlist", help="Display current buyer shortlist under $1,000")
    p_short.set_defaults(func=cmd_shortlist)

    # exceptional command
    p_exc = subparsers.add_parser("exceptional", help="Display exceptional candidates up to $5,000")
    p_exc.set_defaults(func=cmd_exceptional)

    # sources command
    p_src = subparsers.add_parser("sources", help="Audit marketplace adapters and access methods")
    p_src.set_defaults(func=cmd_sources)

    # serve command
    p_srv = subparsers.add_parser("serve", help="Launch interactive browser dashboard")
    p_srv.add_argument("--host", default="127.0.0.1", help="Host address (default 127.0.0.1)")
    p_srv.add_argument("--port", type=int, default=8080, help="Port (default 8080)")
    p_srv.set_defaults(func=cmd_serve)

    # daemon command
    p_dmn = subparsers.add_parser("daemon", help="Run scheduled daemon (08:00 Africa/Casablanca)")
    p_dmn.set_defaults(func=cmd_daemon)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)

if __name__ == "__main__":
    main()
