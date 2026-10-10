"""
Daily Workflow Orchestrator and Scheduler for Acquisition Radar.
Coordinates discovery, deduplication, SEO auditing, financial valuation,
scoring, database persistence, and daily report generation.
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from datetime import timezone as ZoneInfo

from radar.config import config
from radar.models import Listing, SEOMetrics, Valuation, ScoreBreakdown, CompleteOpportunity, DailyRun
from radar.database import db
from radar.adapters.registry import registry
from radar.seo.analyzer import SEOAnalyzer
from radar.valuation import ValuationEngine
from radar.scoring import ScoringEngine
from radar.reporting import ReportGenerator, DeliveryManager

class AcquisitionRadarRunner:
    @classmethod
    async def run_discovery_cycle(cls, include_fixtures: bool = True) -> DailyRun:
        """
        Executes complete end-to-end acquisition research workflow.
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        started_at = datetime.now(timezone.utc).isoformat()

        daily_run = DailyRun(
            run_id=run_id,
            run_date=run_date,
            started_at=started_at
        )

        print(f"[*] Starting Acquisition Radar discovery cycle [{run_id}] for {run_date}...")

        # Step 1: Discover listings from all marketplace adapters
        discovered_listings, source_health = await registry.fetch_all(include_fixtures=include_fixtures)
        daily_run.total_discovered = len(discovered_listings)
        daily_run.source_health = source_health
        print(f"[*] Discovered {len(discovered_listings)} listings across marketplaces.")

        # Step 2: Database upsert, price change detection, and history tracking
        processed_opportunities: List[CompleteOpportunity] = []
        new_count = 0
        price_drop_count = 0
        under_1k_count = 0
        shortlist_count = 0
        watchlist_count = 0
        rejected_count = 0
        exceptional_5k_count = 0

        for listing in discovered_listings:
            # Upsert into database
            persisted_listing, is_new, price_changed = db.upsert_listing(listing)
            if is_new:
                new_count += 1
            if price_changed and persisted_listing.price_change_amount < 0:
                price_drop_count += 1
            if persisted_listing.asking_price <= config.max_normal_budget_usd:
                under_1k_count += 1

            # Step 3: Run SEO Intelligence Audit
            seo = SEOAnalyzer.analyze(persisted_listing)
            db.save_seo(seo)

            # Step 4: Run Financial Valuation & Turnaround Thesis Engine
            valuation = ValuationEngine.evaluate(persisted_listing, seo)
            db.save_valuation(valuation)

            # Step 5: Run 100-Point Scoring Engine
            score = ScoringEngine.evaluate(persisted_listing, seo, valuation)
            db.save_score(score)

            # Tally classifications
            if score.classification == "BUYER_SHORTLIST":
                if score.exceptional_5k_candidate:
                    exceptional_5k_count += 1
                else:
                    shortlist_count += 1
            elif score.classification == "WATCHLIST":
                watchlist_count += 1
            else:
                rejected_count += 1

            complete_opp = CompleteOpportunity(
                listing=persisted_listing,
                seo=seo,
                valuation=valuation,
                score=score
            )
            processed_opportunities.append(complete_opp)

        # Sort opportunities: Shortlists first, ordered by score descending
        processed_opportunities.sort(key=lambda o: (o.score.total_score, -o.listing.asking_price), reverse=True)

        # Find top conviction deal
        if processed_opportunities:
            top_candidates = [
                o for o in processed_opportunities
                if o.score.classification == "BUYER_SHORTLIST"
            ]
            if top_candidates:
                daily_run.most_interesting_deal_id = top_candidates[0].listing.id

        daily_run.new_listings_count = new_count
        daily_run.price_reductions_count = price_drop_count
        daily_run.under_1k_count = under_1k_count
        daily_run.shortlist_count = shortlist_count
        daily_run.watchlist_count = watchlist_count
        daily_run.rejected_count = rejected_count
        daily_run.exceptional_5k_count = exceptional_5k_count

        # Step 6: Generate Markdown & HTML Reports
        print("[*] Generating daily report artifacts...")
        md_report = ReportGenerator.generate_markdown(daily_run, processed_opportunities)
        html_report = ReportGenerator.generate_html(daily_run, processed_opportunities)

        # Step 7: Multi-channel delivery (local disk, email, telegram)
        print("[*] Dispatching reports via configured delivery channels...")
        delivery_res = DeliveryManager.deliver_all(daily_run, md_report, html_report)
        daily_run.delivery_status = delivery_res
        daily_run.completed_at = datetime.now(timezone.utc).isoformat()

        # Step 8: Save Daily Run Summary
        db.save_daily_run(daily_run)

        print(f"[OK] Daily discovery cycle completed successfully!")
        print(f"    - Under $1k Shortlist: {daily_run.shortlist_count} opportunities")
        print(f"    - Exceptional Up to $5k: {daily_run.exceptional_5k_count} opportunities")
        print(f"    - Watchlist: {daily_run.watchlist_count} items")
        print(f"    - Reports generated: {daily_run.report_markdown_path}")

        return daily_run

    @classmethod
    def run_scheduled_daemon(cls):
        """
        Runs the daily acquisition radar on schedule (08:00 Africa/Casablanca time).
        """
        tz_name = config.schedule_timezone
        target_time = config.schedule_time
        print(f"[*] Starting Acquisition Radar Daemon...")
        print(f"[*] Configured Schedule: {target_time} daily ({tz_name})")

        last_executed_day = ""

        while True:
            try:
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo(tz_name)
                    now = datetime.now(tz)
                except Exception:
                    now = datetime.now(timezone.utc)

                current_day = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M")

                if current_time == target_time and current_day != last_executed_day:
                    print(f"[*] Triggering scheduled run for {current_day} at {current_time}...")
                    asyncio.run(cls.run_discovery_cycle())
                    last_executed_day = current_day

                time.sleep(30)
            except KeyboardInterrupt:
                print("\n[*] Scheduler daemon stopped by user.")
                break
            except Exception as e:
                print(f"[!] Error in scheduler loop: {e}")
                time.sleep(60)
