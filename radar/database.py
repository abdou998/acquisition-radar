"""
SQLite Persistence Layer for the Acquisition Radar.
Tracks listings, snapshots, price history, SEO audits, valuations, scores, and daily runs.
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from radar.config import config
from radar.models import Listing, SEOMetrics, Valuation, ScoreBreakdown, CompleteOpportunity, DailyRun

class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.database_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Listings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                asking_price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                original_price REAL,
                monthly_revenue REAL DEFAULT 0.0,
                monthly_profit REAL DEFAULT 0.0,
                monthly_visitors INTEGER DEFAULT 0,
                monthly_pageviews INTEGER DEFAULT 0,
                monthly_search_clicks INTEGER DEFAULT 0,
                subscribers_count INTEGER DEFAULT 0,
                domain TEXT,
                domain_age_years REAL DEFAULT 0.0,
                tech_stack TEXT DEFAULT 'Unknown',
                hours_per_week REAL DEFAULT 2.0,
                monetization_methods TEXT,
                assets_included TEXT,
                seller_claims_verified INTEGER DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                price_change_amount REAL DEFAULT 0.0,
                price_change_percent REAL DEFAULT 0.0,
                raw_metadata TEXT,
                user_status TEXT DEFAULT 'new',
                user_notes TEXT DEFAULT ''
            );
            """)

            # Price history table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            """)

            # SEO metrics table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS seo_metrics (
                listing_id TEXT PRIMARY KEY,
                domain TEXT,
                estimated_monthly_organic_visits INTEGER DEFAULT 0,
                ranking_keywords_count INTEGER DEFAULT 0,
                top_keywords TEXT,
                commercial_intent_ratio REAL DEFAULT 0.2,
                backlinks_count INTEGER DEFAULT 0,
                referring_domains INTEGER DEFAULT 0,
                domain_authority_proxy REAL DEFAULT 10.0,
                indexed_pages INTEGER DEFAULT 0,
                brand_search_ratio REAL DEFAULT 0.1,
                traffic_trend_6m TEXT DEFAULT 'stable',
                traffic_trend_change_pct REAL DEFAULT 0.0,
                serp_competition_level TEXT DEFAULT 'medium',
                ai_overview_vulnerability TEXT DEFAULT 'medium',
                content_gap_opportunity TEXT DEFAULT '',
                seo_health_notes TEXT,
                confidence TEXT DEFAULT 'low',
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            """)

            # Valuations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS valuations (
                listing_id TEXT PRIMARY KEY,
                total_acquisition_cost REAL DEFAULT 0.0,
                escrow_fee_estimate REAL DEFAULT 0.0,
                transfer_fee_estimate REAL DEFAULT 0.0,
                ad_equivalent_value_low REAL DEFAULT 0.0,
                ad_equivalent_value_base REAL DEFAULT 0.0,
                ad_equivalent_value_high REAL DEFAULT 0.0,
                monetization_potential_low REAL DEFAULT 0.0,
                monetization_potential_base REAL DEFAULT 0.0,
                monetization_potential_high REAL DEFAULT 0.0,
                rebuild_cost_estimate REAL DEFAULT 0.0,
                rebuild_months_estimate INTEGER DEFAULT 6,
                valuation_multiple REAL DEFAULT 0.0,
                payback_period_months_conservative REAL DEFAULT 0.0,
                payback_period_months_base REAL DEFAULT 0.0,
                undervaluation_thesis TEXT,
                action_plan_30_days TEXT,
                estimated_improvement_cost REAL DEFAULT 0.0,
                estimated_weekly_hours REAL DEFAULT 4.0,
                due_diligence_checklist TEXT,
                red_flags TEXT,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            """)

            # Scores table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                listing_id TEXT PRIMARY KEY,
                audience_score REAL DEFAULT 0.0,
                seo_score REAL DEFAULT 0.0,
                financial_score REAL DEFAULT 0.0,
                price_score REAL DEFAULT 0.0,
                transfer_score REAL DEFAULT 0.0,
                risk_score REAL DEFAULT 0.0,
                penalties REAL DEFAULT 0.0,
                penalty_reasons TEXT,
                total_score REAL DEFAULT 0.0,
                classification TEXT DEFAULT 'REJECTED',
                rejection_reasons TEXT,
                exceptional_5k_candidate INTEGER DEFAULT 0,
                exceptional_justification TEXT,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            );
            """)

            # Daily runs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_runs (
                run_id TEXT PRIMARY KEY,
                run_date TEXT NOT NULL,
                total_discovered INTEGER DEFAULT 0,
                new_listings_count INTEGER DEFAULT 0,
                price_reductions_count INTEGER DEFAULT 0,
                under_1k_count INTEGER DEFAULT 0,
                shortlist_count INTEGER DEFAULT 0,
                watchlist_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                exceptional_5k_count INTEGER DEFAULT 0,
                most_interesting_deal_id TEXT,
                report_markdown_path TEXT,
                report_html_path TEXT,
                delivery_status TEXT,
                source_health TEXT,
                started_at TEXT,
                completed_at TEXT
            );
            """)

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_url ON listings(url);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_domain ON listings(domain);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(asking_price);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_classification ON scores(classification);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_total ON scores(total_score);")
            conn.commit()

    def upsert_listing(self, listing: Listing) -> Tuple[Listing, bool, bool]:
        """
        Inserts or updates a listing.
        Returns: (updated_listing, is_new, price_changed)
        """
        now_str = datetime.now(timezone.utc).isoformat()
        is_new = False
        price_changed = False

        # Sanitize metrics to valid SQLite integer and float boundaries
        listing.monthly_visitors = int(min(max(listing.monthly_visitors or 0, 0), 2_000_000_000))
        listing.monthly_pageviews = int(min(max(listing.monthly_pageviews or 0, 0), 2_000_000_000))
        listing.monthly_search_clicks = int(min(max(listing.monthly_search_clicks or 0, 0), 2_000_000_000))
        listing.subscribers_count = int(min(max(listing.subscribers_count or 0, 0), 2_000_000_000))
        listing.asking_price = float(min(max(listing.asking_price or 0.0, 0.0), 100_000_000.0))
        if listing.original_price is not None:
            listing.original_price = float(min(max(listing.original_price, 0.0), 100_000_000.0))
        listing.monthly_revenue = float(min(max(listing.monthly_revenue or 0.0, 0.0), 100_000_000.0))
        listing.monthly_profit = float(min(max(listing.monthly_profit or 0.0, -100_000_000.0), 100_000_000.0))
        listing.hours_per_week = float(min(max(listing.hours_per_week or 0.0, 0.0), 168.0))
        listing.domain_age_years = float(min(max(listing.domain_age_years or 0.0, 0.0), 100.0))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, asking_price, original_price, first_seen_at FROM listings WHERE url = ?", (listing.url,))
            row = cursor.fetchone()

            if row:
                old_id = row["id"]
                listing.id = old_id
                old_price = float(row["asking_price"])
                original_price = float(row["original_price"]) if row["original_price"] is not None else old_price
                listing.first_seen_at = row["first_seen_at"]
                listing.last_seen_at = now_str
                listing.original_price = original_price

                if abs(listing.asking_price - old_price) > 0.01:
                    price_changed = True
                    listing.price_change_amount = listing.asking_price - old_price
                    listing.price_change_percent = ((listing.asking_price - old_price) / old_price) * 100.0 if old_price > 0 else 0.0
                    if listing.asking_price < old_price:
                        listing.status = "price_reduced"
                    # record price history
                    cursor.execute(
                        "INSERT INTO price_history (listing_id, price, currency, recorded_at) VALUES (?, ?, ?, ?)",
                        (listing.id, listing.asking_price, listing.currency, now_str)
                    )
                else:
                    listing.price_change_amount = 0.0
                    listing.price_change_percent = 0.0

                cursor.execute("""
                UPDATE listings SET
                    title = ?, description = ?, category = ?, asking_price = ?, currency = ?,
                    original_price = ?, monthly_revenue = ?, monthly_profit = ?, monthly_visitors = ?,
                    monthly_pageviews = ?, monthly_search_clicks = ?, subscribers_count = ?,
                    domain = ?, domain_age_years = ?, tech_stack = ?, hours_per_week = ?,
                    monetization_methods = ?, assets_included = ?, seller_claims_verified = ?,
                    last_seen_at = ?, status = ?, price_change_amount = ?, price_change_percent = ?,
                    raw_metadata = ?
                WHERE id = ?
                """, (
                    listing.title, listing.description, listing.category, listing.asking_price, listing.currency,
                    listing.original_price, listing.monthly_revenue, listing.monthly_profit, listing.monthly_visitors,
                    listing.monthly_pageviews, listing.monthly_search_clicks, listing.subscribers_count,
                    listing.domain, listing.domain_age_years, listing.tech_stack, listing.hours_per_week,
                    json.dumps(listing.monetization_methods), json.dumps(listing.assets_included),
                    1 if listing.seller_claims_verified else 0, listing.last_seen_at, listing.status,
                    listing.price_change_amount, listing.price_change_percent, json.dumps(listing.raw_metadata),
                    listing.id
                ))
            else:
                is_new = True
                listing.original_price = listing.asking_price
                listing.first_seen_at = now_str
                listing.last_seen_at = now_str
                listing.status = "active"

                cursor.execute("""
                INSERT INTO listings (
                    id, source, external_id, url, title, description, category, asking_price, currency,
                    original_price, monthly_revenue, monthly_profit, monthly_visitors, monthly_pageviews,
                    monthly_search_clicks, subscribers_count, domain, domain_age_years, tech_stack,
                    hours_per_week, monetization_methods, assets_included, seller_claims_verified,
                    first_seen_at, last_seen_at, status, price_change_amount, price_change_percent, raw_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    listing.id, listing.source, listing.external_id, listing.url, listing.title, listing.description,
                    listing.category, listing.asking_price, listing.currency, listing.original_price,
                    listing.monthly_revenue, listing.monthly_profit, listing.monthly_visitors, listing.monthly_pageviews,
                    listing.monthly_search_clicks, listing.subscribers_count, listing.domain, listing.domain_age_years,
                    listing.tech_stack, listing.hours_per_week, json.dumps(listing.monetization_methods),
                    json.dumps(listing.assets_included), 1 if listing.seller_claims_verified else 0,
                    listing.first_seen_at, listing.last_seen_at, listing.status, listing.price_change_amount,
                    listing.price_change_percent, json.dumps(listing.raw_metadata)
                ))

                cursor.execute(
                    "INSERT INTO price_history (listing_id, price, currency, recorded_at) VALUES (?, ?, ?, ?)",
                    (listing.id, listing.asking_price, listing.currency, now_str)
                )

            conn.commit()

        return listing, is_new, price_changed

    def save_seo(self, seo: SEOMetrics):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO seo_metrics (
                listing_id, domain, estimated_monthly_organic_visits, ranking_keywords_count,
                top_keywords, commercial_intent_ratio, backlinks_count, referring_domains,
                domain_authority_proxy, indexed_pages, brand_search_ratio, traffic_trend_6m,
                traffic_trend_change_pct, serp_competition_level, ai_overview_vulnerability,
                content_gap_opportunity, seo_health_notes, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(listing_id) DO UPDATE SET
                domain = excluded.domain,
                estimated_monthly_organic_visits = excluded.estimated_monthly_organic_visits,
                ranking_keywords_count = excluded.ranking_keywords_count,
                top_keywords = excluded.top_keywords,
                commercial_intent_ratio = excluded.commercial_intent_ratio,
                backlinks_count = excluded.backlinks_count,
                referring_domains = excluded.referring_domains,
                domain_authority_proxy = excluded.domain_authority_proxy,
                indexed_pages = excluded.indexed_pages,
                brand_search_ratio = excluded.brand_search_ratio,
                traffic_trend_6m = excluded.traffic_trend_6m,
                traffic_trend_change_pct = excluded.traffic_trend_change_pct,
                serp_competition_level = excluded.serp_competition_level,
                ai_overview_vulnerability = excluded.ai_overview_vulnerability,
                content_gap_opportunity = excluded.content_gap_opportunity,
                seo_health_notes = excluded.seo_health_notes,
                confidence = excluded.confidence
            """, (
                seo.listing_id, seo.domain, seo.estimated_monthly_organic_visits, seo.ranking_keywords_count,
                json.dumps(seo.top_keywords), seo.commercial_intent_ratio, seo.backlinks_count,
                seo.referring_domains, seo.domain_authority_proxy, seo.indexed_pages, seo.brand_search_ratio,
                seo.traffic_trend_6m, seo.traffic_trend_change_pct, seo.serp_competition_level,
                seo.ai_overview_vulnerability, seo.content_gap_opportunity, json.dumps(seo.seo_health_notes),
                seo.confidence
            ))
            conn.commit()

    def save_valuation(self, val: Valuation):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO valuations (
                listing_id, total_acquisition_cost, escrow_fee_estimate, transfer_fee_estimate,
                ad_equivalent_value_low, ad_equivalent_value_base, ad_equivalent_value_high,
                monetization_potential_low, monetization_potential_base, monetization_potential_high,
                rebuild_cost_estimate, rebuild_months_estimate, valuation_multiple,
                payback_period_months_conservative, payback_period_months_base,
                undervaluation_thesis, action_plan_30_days, estimated_improvement_cost,
                estimated_weekly_hours, due_diligence_checklist, red_flags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(listing_id) DO UPDATE SET
                total_acquisition_cost = excluded.total_acquisition_cost,
                escrow_fee_estimate = excluded.escrow_fee_estimate,
                transfer_fee_estimate = excluded.transfer_fee_estimate,
                ad_equivalent_value_low = excluded.ad_equivalent_value_low,
                ad_equivalent_value_base = excluded.ad_equivalent_value_base,
                ad_equivalent_value_high = excluded.ad_equivalent_value_high,
                monetization_potential_low = excluded.monetization_potential_low,
                monetization_potential_base = excluded.monetization_potential_base,
                monetization_potential_high = excluded.monetization_potential_high,
                rebuild_cost_estimate = excluded.rebuild_cost_estimate,
                rebuild_months_estimate = excluded.rebuild_months_estimate,
                valuation_multiple = excluded.valuation_multiple,
                payback_period_months_conservative = excluded.payback_period_months_conservative,
                payback_period_months_base = excluded.payback_period_months_base,
                undervaluation_thesis = excluded.undervaluation_thesis,
                action_plan_30_days = excluded.action_plan_30_days,
                estimated_improvement_cost = excluded.estimated_improvement_cost,
                estimated_weekly_hours = excluded.estimated_weekly_hours,
                due_diligence_checklist = excluded.due_diligence_checklist,
                red_flags = excluded.red_flags
            """, (
                val.listing_id, val.total_acquisition_cost, val.escrow_fee_estimate, val.transfer_fee_estimate,
                val.ad_equivalent_value_low, val.ad_equivalent_value_base, val.ad_equivalent_value_high,
                val.monetization_potential_low, val.monetization_potential_base, val.monetization_potential_high,
                val.rebuild_cost_estimate, val.rebuild_months_estimate, val.valuation_multiple,
                val.payback_period_months_conservative, val.payback_period_months_base,
                val.undervaluation_thesis, json.dumps(val.action_plan_30_days),
                val.estimated_improvement_cost, val.estimated_weekly_hours,
                json.dumps(val.due_diligence_checklist), json.dumps(val.red_flags)
            ))
            conn.commit()

    def save_score(self, score: ScoreBreakdown):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO scores (
                listing_id, audience_score, seo_score, financial_score, price_score,
                transfer_score, risk_score, penalties, penalty_reasons, total_score,
                classification, rejection_reasons, exceptional_5k_candidate, exceptional_justification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(listing_id) DO UPDATE SET
                audience_score = excluded.audience_score,
                seo_score = excluded.seo_score,
                financial_score = excluded.financial_score,
                price_score = excluded.price_score,
                transfer_score = excluded.transfer_score,
                risk_score = excluded.risk_score,
                penalties = excluded.penalties,
                penalty_reasons = excluded.penalty_reasons,
                total_score = excluded.total_score,
                classification = excluded.classification,
                rejection_reasons = excluded.rejection_reasons,
                exceptional_5k_candidate = excluded.exceptional_5k_candidate,
                exceptional_justification = excluded.exceptional_justification
            """, (
                score.listing_id, score.audience_score, score.seo_score, score.financial_score,
                score.price_score, score.transfer_score, score.risk_score, score.penalties,
                json.dumps(score.penalty_reasons), score.total_score, score.classification,
                json.dumps(score.rejection_reasons), 1 if score.exceptional_5k_candidate else 0,
                json.dumps(score.exceptional_justification)
            ))
            conn.commit()

    def save_daily_run(self, run: DailyRun):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO daily_runs (
                run_id, run_date, total_discovered, new_listings_count, price_reductions_count,
                under_1k_count, shortlist_count, watchlist_count, rejected_count,
                exceptional_5k_count, most_interesting_deal_id, report_markdown_path,
                report_html_path, delivery_status, source_health, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                total_discovered = excluded.total_discovered,
                new_listings_count = excluded.new_listings_count,
                price_reductions_count = excluded.price_reductions_count,
                under_1k_count = excluded.under_1k_count,
                shortlist_count = excluded.shortlist_count,
                watchlist_count = excluded.watchlist_count,
                rejected_count = excluded.rejected_count,
                exceptional_5k_count = excluded.exceptional_5k_count,
                most_interesting_deal_id = excluded.most_interesting_deal_id,
                report_markdown_path = excluded.report_markdown_path,
                report_html_path = excluded.report_html_path,
                delivery_status = excluded.delivery_status,
                source_health = excluded.source_health,
                completed_at = excluded.completed_at
            """, (
                run.run_id, run.run_date, run.total_discovered, run.new_listings_count,
                run.price_reductions_count, run.under_1k_count, run.shortlist_count,
                run.watchlist_count, run.rejected_count, run.exceptional_5k_count,
                run.most_interesting_deal_id, run.report_markdown_path, run.report_html_path,
                json.dumps(run.delivery_status), json.dumps(run.source_health),
                run.started_at, run.completed_at
            ))
            conn.commit()

    def _row_to_listing(self, row: sqlite3.Row) -> Listing:
        return Listing(
            id=row["id"],
            source=row["source"],
            external_id=row["external_id"],
            url=row["url"],
            title=row["title"],
            description=row["description"] or "",
            category=row["category"],
            asking_price=float(row["asking_price"]),
            currency=row["currency"],
            original_price=float(row["original_price"]) if row["original_price"] is not None else float(row["asking_price"]),
            monthly_revenue=float(row["monthly_revenue"]),
            monthly_profit=float(row["monthly_profit"]),
            monthly_visitors=int(row["monthly_visitors"]),
            monthly_pageviews=int(row["monthly_pageviews"]),
            monthly_search_clicks=int(row["monthly_search_clicks"]),
            subscribers_count=int(row["subscribers_count"]),
            domain=row["domain"],
            domain_age_years=float(row["domain_age_years"]),
            tech_stack=row["tech_stack"] or "Unknown",
            hours_per_week=float(row["hours_per_week"]),
            monetization_methods=json.loads(row["monetization_methods"] or "[]"),
            assets_included=json.loads(row["assets_included"] or "[]"),
            seller_claims_verified=bool(row["seller_claims_verified"]),
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            status=row["status"],
            price_change_amount=float(row["price_change_amount"]),
            price_change_percent=float(row["price_change_percent"]),
            raw_metadata=json.loads(row["raw_metadata"] or "{}")
        )

    def _row_to_seo(self, row: sqlite3.Row) -> SEOMetrics:
        return SEOMetrics(
            listing_id=row["listing_id"],
            domain=row["domain"],
            estimated_monthly_organic_visits=int(row["estimated_monthly_organic_visits"]),
            ranking_keywords_count=int(row["ranking_keywords_count"]),
            top_keywords=json.loads(row["top_keywords"] or "[]"),
            commercial_intent_ratio=float(row["commercial_intent_ratio"]),
            backlinks_count=int(row["backlinks_count"]),
            referring_domains=int(row["referring_domains"]),
            domain_authority_proxy=float(row["domain_authority_proxy"]),
            indexed_pages=int(row["indexed_pages"]),
            brand_search_ratio=float(row["brand_search_ratio"]),
            traffic_trend_6m=row["traffic_trend_6m"],
            traffic_trend_change_pct=float(row["traffic_trend_change_pct"]),
            serp_competition_level=row["serp_competition_level"],
            ai_overview_vulnerability=row["ai_overview_vulnerability"],
            content_gap_opportunity=row["content_gap_opportunity"] or "",
            seo_health_notes=json.loads(row["seo_health_notes"] or "[]"),
            confidence=row["confidence"]
        )

    def _row_to_valuation(self, row: sqlite3.Row) -> Valuation:
        return Valuation(
            listing_id=row["listing_id"],
            total_acquisition_cost=float(row["total_acquisition_cost"]),
            escrow_fee_estimate=float(row["escrow_fee_estimate"]),
            transfer_fee_estimate=float(row["transfer_fee_estimate"]),
            ad_equivalent_value_low=float(row["ad_equivalent_value_low"]),
            ad_equivalent_value_base=float(row["ad_equivalent_value_base"]),
            ad_equivalent_value_high=float(row["ad_equivalent_value_high"]),
            monetization_potential_low=float(row["monetization_potential_low"]),
            monetization_potential_base=float(row["monetization_potential_base"]),
            monetization_potential_high=float(row["monetization_potential_high"]),
            rebuild_cost_estimate=float(row["rebuild_cost_estimate"]),
            rebuild_months_estimate=int(row["rebuild_months_estimate"]),
            valuation_multiple=float(row["valuation_multiple"]),
            payback_period_months_conservative=float(row["payback_period_months_conservative"]),
            payback_period_months_base=float(row["payback_period_months_base"]),
            undervaluation_thesis=row["undervaluation_thesis"] or "",
            action_plan_30_days=json.loads(row["action_plan_30_days"] or "[]"),
            estimated_improvement_cost=float(row["estimated_improvement_cost"]),
            estimated_weekly_hours=float(row["estimated_weekly_hours"]),
            due_diligence_checklist=json.loads(row["due_diligence_checklist"] or "[]"),
            red_flags=json.loads(row["red_flags"] or "[]")
        )

    def _row_to_score(self, row: sqlite3.Row) -> ScoreBreakdown:
        return ScoreBreakdown(
            listing_id=row["listing_id"],
            audience_score=float(row["audience_score"]),
            seo_score=float(row["seo_score"]),
            financial_score=float(row["financial_score"]),
            price_score=float(row["price_score"]),
            transfer_score=float(row["transfer_score"]),
            risk_score=float(row["risk_score"]),
            penalties=float(row["penalties"]),
            penalty_reasons=json.loads(row["penalty_reasons"] or "[]"),
            total_score=float(row["total_score"]),
            classification=row["classification"],
            rejection_reasons=json.loads(row["rejection_reasons"] or "[]"),
            exceptional_5k_candidate=bool(row["exceptional_5k_candidate"]),
            exceptional_justification=json.loads(row["exceptional_justification"] or "{}")
        )

    def get_complete_opportunity(self, listing_id: str) -> Optional[CompleteOpportunity]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
            l_row = cursor.fetchone()
            if not l_row:
                return None
            listing = self._row_to_listing(l_row)

            cursor.execute("SELECT * FROM seo_metrics WHERE listing_id = ?", (listing_id,))
            s_row = cursor.fetchone()
            seo = self._row_to_seo(s_row) if s_row else SEOMetrics(listing_id=listing_id, domain=listing.domain)

            cursor.execute("SELECT * FROM valuations WHERE listing_id = ?", (listing_id,))
            v_row = cursor.fetchone()
            valuation = self._row_to_valuation(v_row) if v_row else Valuation(listing_id=listing_id)

            cursor.execute("SELECT * FROM scores WHERE listing_id = ?", (listing_id,))
            sc_row = cursor.fetchone()
            score = self._row_to_score(sc_row) if sc_row else ScoreBreakdown(listing_id=listing_id)

            return CompleteOpportunity(listing=listing, seo=seo, valuation=valuation, score=score)

    def get_all_complete_opportunities(
        self,
        classification: Optional[str] = None,
        max_price: Optional[float] = None,
        min_score: Optional[float] = None,
        status: Optional[str] = None
    ) -> List[CompleteOpportunity]:
        query = """
        SELECT l.id FROM listings l
        LEFT JOIN scores sc ON l.id = sc.listing_id
        WHERE 1=1
        """
        params = []

        if classification:
            query += " AND sc.classification = ?"
            params.append(classification)
        if max_price is not None:
            query += " AND l.asking_price <= ?"
            params.append(max_price)
        if min_score is not None:
            query += " AND sc.total_score >= ?"
            params.append(min_score)
        if status:
            query += " AND l.status = ?"
            params.append(status)

        query += " ORDER BY sc.total_score DESC, l.asking_price ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for r in rows:
            opp = self.get_complete_opportunity(r["id"])
            if opp:
                results.append(opp)
        return results

    def get_price_history(self, listing_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT price, currency, recorded_at FROM price_history WHERE listing_id = ? ORDER BY recorded_at ASC",
                (listing_id,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def update_user_status(self, listing_id: str, user_status: str, user_notes: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_notes is not None:
                cursor.execute(
                    "UPDATE listings SET user_status = ?, user_notes = ? WHERE id = ?",
                    (user_status, user_notes, listing_id)
                )
            else:
                cursor.execute(
                    "UPDATE listings SET user_status = ? WHERE id = ?",
                    (user_status, listing_id)
                )
            conn.commit()

    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_runs ORDER BY started_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def count_active_listings(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM listings WHERE status IN ('active', 'price_reduced')")
            return cursor.fetchone()[0]

db = Database()
