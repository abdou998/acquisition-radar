"""
SMTP Email Test Helper.
Quickly validates your email configuration from .env or command-line parameters.
"""

import sys
from radar.config import config
from radar.reporting.delivery import DeliveryManager

def test_email():
    print("=" * 60)
    print("   ACQUISITION RADAR -- EMAIL CONFIGURATION TEST")
    print("=" * 60)
    print(f"- Email Enabled:    {config.enable_email}")
    print(f"- SMTP Host:        {config.smtp_host or '[NOT SET]'}")
    print(f"- SMTP Port:        {config.smtp_port}")
    print(f"- SMTP User:        {config.smtp_user or '[NOT SET]'}")
    print(f"- Recipient:        {config.email_recipient or '[NOT SET]'}")
    print("-" * 60)

    if not config.enable_email:
        print("\n[!] RADAR_ENABLE_EMAIL is currently set to 'false' in .env.")
        print("    To enable email sending, edit .env and set:")
        print("    RADAR_ENABLE_EMAIL=true\n")
        return

    if not (config.smtp_host and config.smtp_user and config.smtp_password and config.email_recipient):
        print("\n[!] Missing SMTP credentials in .env.")
        print("    Please provide:")
        print("    RADAR_SMTP_HOST=smtp.gmail.com")
        print("    RADAR_SMTP_PORT=587")
        print("    RADAR_SMTP_USER=your_email@gmail.com")
        print("    RADAR_SMTP_PASSWORD=your_app_password")
        print("    RADAR_EMAIL_RECIPIENT=your_email@gmail.com\n")
        return

    print("[*] Sending test email...")
    subject = "🎯 Acquisition Radar: Test Email Connection"
    text_content = "This is a test notification from your Daily Acquisition Radar. If you received this, your email configuration is working perfectly!"
    html_content = """
    <html>
      <body style="font-family: sans-serif; padding: 20px; color: #1e293b;">
        <h2 style="color: #2563eb;">🎯 Daily Acquisition Radar Test</h2>
        <p>If you received this email, your <strong>cloud email delivery pipeline is ready</strong>!</p>
        <p>Your daily reports will be delivered directly to this address at <strong>08:00 Africa/Casablanca time</strong>.</p>
      </body>
    </html>
    """

    res = DeliveryManager.send_email(subject, text_content, html_content)
    print("Result:", res)

    if res.get("status") == "delivered":
        print("\n[OK] Success! Test email delivered to:", config.email_recipient)
    else:
        print("\n[FAILED] Error details:", res.get("error", res.get("reason")))

if __name__ == "__main__":
    test_email()
