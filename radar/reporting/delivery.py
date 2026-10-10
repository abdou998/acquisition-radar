"""
Multi-Channel Report Delivery Engine.
Handles local file output, optional SMTP email dispatch, and optional Telegram bot notifications.
Never claims a message was delivered if credentials were not present or delivery failed.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

from radar.config import config
from radar.models import DailyRun

class DeliveryManager:
    @staticmethod
    def save_local_reports(run_date: str, md_content: str, html_content: str) -> Dict[str, str]:
        """
        Saves reports locally to configured reports directory.
        """
        reports_dir = Path(config.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        md_path = reports_dir / f"daily_report_{run_date}.md"
        html_path = reports_dir / f"daily_report_{run_date}.html"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "markdown_path": str(md_path),
            "html_path": str(html_path)
        }

    @staticmethod
    def send_email(subject: str, text_content: str, html_content: str) -> Dict[str, Any]:
        """
        Dispatches email via SMTP if configured.
        """
        if not config.enable_email:
            return {"status": "skipped", "reason": "RADAR_ENABLE_EMAIL is disabled"}

        if not (config.smtp_host and config.smtp_user and config.smtp_password and config.email_recipient):
            return {
                "status": "skipped",
                "reason": "Incomplete SMTP configuration in .env (requires RADAR_SMTP_HOST, USER, PASSWORD, RECIPIENT)"
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = config.smtp_sender or config.smtp_user
            msg["To"] = config.email_recipient

            part_text = MIMEText(text_content, "plain", "utf-8")
            part_html = MIMEText(html_content, "html", "utf-8")
            msg.attach(part_text)
            msg.attach(part_html)

            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(config.smtp_user, config.smtp_password)
                server.send_message(msg)

            return {"status": "delivered", "recipient": config.email_recipient}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def send_telegram(message_text: str) -> Dict[str, Any]:
        """
        Dispatches summary notification to Telegram bot if configured.
        """
        if not config.enable_telegram:
            return {"status": "skipped", "reason": "RADAR_ENABLE_TELEGRAM is disabled"}

        if not (config.telegram_bot_token and config.telegram_chat_id):
            return {
                "status": "skipped",
                "reason": "Missing RADAR_TELEGRAM_BOT_TOKEN or RADAR_TELEGRAM_CHAT_ID in .env"
            }

        url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": config.telegram_chat_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return {"status": "delivered"}
                else:
                    return {"status": "failed", "status_code": resp.status_code, "response": resp.text}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    @classmethod
    def deliver_all(cls, run: DailyRun, md_content: str, html_content: str) -> Dict[str, Any]:
        """
        Executes complete delivery pipeline: local storage, email, and telegram.
        """
        delivery_results = {}

        # 1. Local disk output (always performed)
        paths = cls.save_local_reports(run.run_date, md_content, html_content)
        delivery_results["local_files"] = {"status": "saved", **paths}
        run.report_markdown_path = paths["markdown_path"]
        run.report_html_path = paths["html_path"]

        # 2. Email delivery
        subject = f"🎯 Acquisition Radar Daily: {run.shortlist_count} Deals Under $1k ({run.run_date})"
        delivery_results["email"] = cls.send_email(subject, md_content, html_content)

        # 3. Telegram notification
        telegram_summary = (
            f"🎯 *Acquisition Radar Report ({run.run_date})*\n\n"
            f"• Audited: {run.total_discovered} listings\n"
            f"• Shortlist &le; $1k: *{run.shortlist_count} deals*\n"
            f"• Exceptional &le; $5k: *{run.exceptional_5k_count} deals*\n"
            f"• Price Reductions: {run.price_reductions_count}\n\n"
            f"📄 Full report saved to: `{paths['markdown_path']}`"
        )
        delivery_results["telegram"] = cls.send_telegram(telegram_summary)

        return delivery_results
