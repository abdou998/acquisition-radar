"""
Lightweight Web Dashboard Server for Acquisition Radar.
Built with Python standard library ThreadingHTTPServer. Zero external server dependencies.
Provides interactive browsing, due diligence modal dossiers, and real-time execution triggering.
"""

import json
import asyncio
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any
from jinja2 import Template

from radar.database import db
from radar.config import config
from radar.scheduler.runner import AcquisitionRadarRunner

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "dashboard.html"

class RadarDashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_text: str, status: int = 200):
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_path = self.path.split("?")[0]

        if parsed_path == "/" or parsed_path == "/index.html":
            opportunities = db.get_all_complete_opportunities()
            deals_data = [o.to_dict() for o in opportunities]

            shortlist_count = sum(1 for o in opportunities if o.score.classification == "BUYER_SHORTLIST" and not o.score.exceptional_5k_candidate and o.listing.asking_price <= config.max_normal_budget_usd)
            exceptional_count = sum(1 for o in opportunities if o.score.exceptional_5k_candidate)
            drops_count = sum(1 for o in opportunities if o.listing.price_change_amount < 0)

            with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template_str = f.read()

            t = Template(template_str)
            html = t.render(
                total_count=len(opportunities),
                shortlist_count=shortlist_count,
                exceptional_count=exceptional_count,
                drops_count=drops_count,
                deals_json=json.dumps(deals_data)
            )
            self._send_html(html)

        elif parsed_path == "/api/opportunities":
            opportunities = db.get_all_complete_opportunities()
            self._send_json([o.to_dict() for o in opportunities])

        elif parsed_path == "/api/stats":
            runs = db.get_recent_runs(5)
            self._send_json({
                "active_listings": db.count_active_listings(),
                "recent_runs": runs
            })
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_path = self.path.split("?")[0]

        if parsed_path == "/api/run":
            try:
                # Trigger discovery cycle synchronously in thread
                daily_run = asyncio.run(AcquisitionRadarRunner.run_discovery_cycle())
                self._send_json({
                    "status": "success",
                    "run_id": daily_run.run_id,
                    "shortlist_count": daily_run.shortlist_count
                })
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, status=500)

        elif parsed_path == "/api/update_status":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                data = json.loads(body)
                listing_id = data.get("listing_id")
                new_status = data.get("status")
                notes = data.get("notes")

                if listing_id and new_status:
                    db.update_user_status(listing_id, new_status, notes)
                    self._send_json({"status": "success"})
                else:
                    self._send_json({"status": "error", "message": "Missing parameters"}, status=400)
            except Exception as e:
                self._send_json({"status": "error", "error": str(e)}, status=500)
        else:
            self.send_error(404, "Not Found")

def start_ui_server(host: str = "127.0.0.1", port: int = 8080):
    server = ThreadingHTTPServer((host, port), RadarDashboardHandler)
    print(f"[*] Acquisition Radar Dashboard running at: http://{host}:{port}")
    print(f"[*] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping dashboard server...")
        server.shutdown()
