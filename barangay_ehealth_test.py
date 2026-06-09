"""
barangay_ehealth_test.py - Test if your email configuration works (branded)

Usage:
  1. Create a .env file in the project root with MAIL_USERNAME and MAIL_PASSWORD (use Gmail App Password).
  2. Run: python barangay_ehealth_test.py
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import MAIL_CONFIG


def test_email():
    mail_cfg = MAIL_CONFIG
    username = mail_cfg.get('MAIL_USERNAME')
    password = mail_cfg.get('MAIL_PASSWORD')
    server_host = mail_cfg.get('MAIL_SERVER', 'smtp.gmail.com')
    server_port = mail_cfg.get('MAIL_PORT', 587)

    print("📧 Testing email configuration...")

    if not username or not password:
        print("❌ MAIL_USERNAME or MAIL_PASSWORD not set. Add them to your .env file.")
        return

    try:
        print(f"🔌 Connecting to SMTP server {server_host}:{server_port}...")
        server = smtplib.SMTP(server_host, server_port)
        server.starttls()

        print("🔐 Logging in...")
        server.login(username, password)

        print("✅ Login successful! Email configuration works!")

        # Send a test email to yourself
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = "Barangay Sto. Niño E-Health - Test Message"

        body = "Hello! This is a test message from Barangay Sto. Niño E-Health. Your email configuration is working correctly!"
        msg.attach(MIMEText(body, 'plain'))

        server.send_message(msg)
        print(f"✅ Test email sent to {username}")

        server.quit()
        print("🎉 Email system is ready to use!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible issues:")
        print("1. App password may be incorrect or expired")
        print("2. 2-Step Verification must be enabled and use an App Password")
        print("3. Network/Firewall blocking SMTP port 587")


if __name__ == "__main__":
    test_email()
