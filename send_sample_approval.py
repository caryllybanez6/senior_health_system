"""
send_sample_approval.py - Send a sample approval email using NotificationSystem

Usage:
  python send_sample_approval.py

This will send an approval email to the address set in MAIL_CONFIG['MAIL_USERNAME']
"""

from notification import NotificationSystem
from config import MAIL_CONFIG
import time


def main():
    mail_cfg = MAIL_CONFIG
    if not mail_cfg.get('MAIL_USERNAME') or not mail_cfg.get('MAIL_PASSWORD'):
        print("❌ MAIL_USERNAME or MAIL_PASSWORD not configured in .env. Please set them and retry.")
        return

    notifier = NotificationSystem(mail_cfg)

    # Send sample approval email to the configured address
    to_email = mail_cfg.get('MAIL_USERNAME')
    senior_name = "Juan Dela Cruz"
    queue_number = "A-012"
    priority_level = "HIGH"
    appointment_date = "2026-06-01"
    appointment_time = "09:30"
    service_type = "General Consultation"

    print(f"Sending sample approval email to {to_email}...")
    notifier.send_appointment_approved(
        senior_name,
        to_email,
        queue_number,
        priority_level,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        service_type=service_type
    )

    print("Email queued (may be sent asynchronously). Waiting briefly for delivery...")
    time.sleep(5)
    print("Done. Check your inbox/spam for the sample approval email.")


if __name__ == '__main__':
    main()
