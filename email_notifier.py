"""
EMAIL NOTIFICATION SYSTEM - Appointment Confirmation
Sends email to senior immediately after booking
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
import threading
from datetime import datetime

class EmailNotifier:
    def __init__(self, mail_config):
        self.mail_config = mail_config
        self.is_configured = bool(
            mail_config.get('MAIL_USERNAME') and 
            mail_config.get('MAIL_PASSWORD') and
            mail_config.get('MAIL_USERNAME') != ''
        )
    
    def _find_logo_path(self):
        """Return the first available logo path from supported file names."""
        logo_names = ['logo.png', 'logo.jpg', 'logo.jpeg', 'logo.gif']
        base_dirs = [
            os.path.join(os.path.dirname(__file__), 'static', 'images'),
            os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'static', 'images'))
        ]
        for base_dir in base_dirs:
            for name in logo_names:
                logo_path = os.path.join(base_dir, name)
                if os.path.exists(logo_path):
                    return logo_path
        return None

    def send_booking_confirmation(self, senior_name, senior_email, appointment_date, 
                                   appointment_time, service_type, appointment_id,
                                   priority_score=None, is_emergency=False):
        
        if not self.is_configured:
            print(f"⚠️ Email not configured - would send to: {senior_email}")
            return False
        
        # Format date and time nicely
        try:
            formatted_date = datetime.strptime(appointment_date, '%Y-%m-%d').strftime('%B %d, %Y')
        except:
            formatted_date = appointment_date
        
        try:
            formatted_time = datetime.strptime(appointment_time, '%H:%M').strftime('%I:%M %p')
        except:
            formatted_time = appointment_time
        
        # Determine priority level
        if is_emergency:
            priority_text = "🚨 URGENT - Emergency Priority"
            priority_color = "#dc3545"
        elif priority_score and priority_score >= 200:
            priority_text = "🔴 HIGH PRIORITY"
            priority_color = "#fd7e14"
        elif priority_score and priority_score >= 100:
            priority_text = "🟡 MEDIUM PRIORITY"
            priority_color = "#ffc107"
        else:
            priority_text = "🟢 NORMAL PRIORITY"
            priority_color = "#28a745"
        
        subject = f"Appointment Confirmation - Barangay Sto. Niño Health Center"
        logo_path = self._find_logo_path()
        logo_html = ''
        if logo_path:
            logo_html = '<img src="cid:logo" alt="Barangay Sto. Niño Logo" style="max-height: 80px; display:block; margin: 0 auto 15px;" />'
        
        # HTML Email
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 550px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: white;">
                <div style="text-align: center; padding-bottom: 15px; border-bottom: 3px solid #2c7da0;">
                    {logo_html}
                    <h2 style="color: #2c7da0; margin: 0;">🏥 Barangay Sto. Niño</h2>
                    <p style="margin: 5px 0 0;">Health Center - AI e-Health System</p>
                </div>
                
                <div style="padding: 20px 0;">
                    <p>Dear <strong>{senior_name}</strong>,</p>
                    <p><strong>✅ Your health appointment has been successfully booked!</strong></p>
                    
                    <div style="background: #f0f7fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <p style="margin: 0 0 10px; font-weight: bold;">📋 APPOINTMENT DETAILS:</p>
                        <p style="margin: 5px 0;">🏥 Service: <strong>{service_type}</strong></p>
                        <p style="margin: 5px 0;">📅 Date: <strong>{formatted_date}</strong></p>
                        <p style="margin: 5px 0;">⏰ Time: <strong>{formatted_time}</strong></p>
                        <p style="margin: 5px 0;">🔢 Reference: <strong>APT-{appointment_id:06d}</strong></p>
                        <p style="margin: 5px 0;">⚡ Priority: <span style="background:{priority_color}; color:white; padding:3px 8px; border-radius:15px; font-size:12px;">{priority_text}</span></p>
                    </div>
                    
                    <div style="background: #e8f5e9; padding: 12px; border-radius: 8px; margin: 15px 0;">
                        <p style="margin: 0 0 5px; font-weight: bold;">📌 IMPORTANT REMINDERS:</p>
                        <ul style="margin: 5px 0 0 20px;">
                            <li>Please arrive 15 minutes before your schedule</li>
                            <li>Bring your Senior Citizen ID</li>
                            <li>Bring any medications or medical records</li>
                        </ul>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 12px; border-radius: 8px; margin: 15px 0;">
                        <p style="margin: 0; font-weight: bold;">📌 NEXT STEPS:</p>
                        <ol style="margin: 5px 0 0 20px;">
                            <li>Admin will review your appointment</li>
                            <li>You'll receive an email when approved</li>
                            <li>Check your queue number after approval</li>
                        </ol>
                    </div>
                    
                    <hr>
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        📍 Barangay Sto. Niño Hall | 📞 (02) 1234-5678<br>
                        <em>This is an automated message. Please do not reply.</em>
                    </p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Plain text version
        text_content = f"""
BARANGAY STO. NIÑO HEALTH CENTER
================================

Dear {senior_name},

✅ Your health appointment has been successfully booked!

APPOINTMENT DETAILS:
- Service: {service_type}
- Date: {formatted_date}
- Time: {formatted_time}
- Reference: APT-{appointment_id:06d}
- Priority: {priority_text}

IMPORTANT REMINDERS:
- Please arrive 15 minutes before your schedule
- Bring your Senior Citizen ID
- Bring any medications or medical records

NEXT STEPS:
1. Admin will review your appointment
2. You'll receive an email when approved
3. Check your queue number after approval

📍 Barangay Sto. Niño Hall | 📞 (02) 1234-5678
This is an automated message. Please do not reply.
        """
        
        # Send email in background
        logo_path = self._find_logo_path()
        thread = threading.Thread(
            target=self._send_email,
            args=(senior_email, subject, html_content, text_content, logo_path)
        )
        thread.daemon = True
        thread.start()
        
        print(f"📧 Email queued for: {senior_email}")
        return True
    
    def _send_email(self, to_email, subject, html_content, text_content, logo_path=None):
        """Actually send the email"""
        if not self.is_configured:
            print(f"⚠️ Email not configured. Skipping email to {to_email}")
            return False

        try:
            msg = MIMEMultipart('related')
            msg['From'] = self.mail_config['MAIL_USERNAME']
            msg['To'] = to_email
            msg['Subject'] = subject

            alt = MIMEMultipart('alternative')
            alt.attach(MIMEText(text_content, 'plain'))
            alt.attach(MIMEText(html_content, 'html'))
            msg.attach(alt)

            if logo_path:
                try:
                    with open(logo_path, 'rb') as f:
                        img_data = f.read()
                    extension = os.path.splitext(logo_path)[1].lower()
                    if extension in {'.jpg', '.jpeg'}:
                        subtype = 'jpeg'
                    elif extension == '.png':
                        subtype = 'png'
                    elif extension == '.gif':
                        subtype = 'gif'
                    else:
                        subtype = 'octet-stream'
                    img = MIMEImage(img_data, _subtype=subtype)
                    img.add_header('Content-ID', '<logo>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(logo_path))
                    msg.attach(img)
                except Exception:
                    pass

            server = smtplib.SMTP(self.mail_config.get('MAIL_SERVER', 'smtp.gmail.com'), self.mail_config.get('MAIL_PORT', 587))
            server.starttls()
            server.login(self.mail_config['MAIL_USERNAME'], self.mail_config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()

            print(f"✅ Appointment confirmation email sent to: {to_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False