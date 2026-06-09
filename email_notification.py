"""
EMAIL NOTIFICATION SYSTEM
Separate module for handling email notifications after appointment booking
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import threading
import os
from datetime import datetime

class EmailNotification:
    """
    Handles email notifications specifically for appointment confirmations
    Separate from existing notification system to ensure clarity and reliability
    """
    
    def __init__(self, mail_config):
        """
        Initialize email notification system
        
        Args:
            mail_config (dict): Email configuration with MAIL_USERNAME, MAIL_PASSWORD, MAIL_SERVER, MAIL_PORT
        """
        self.mail_config = mail_config
        self.is_configured = bool(
            mail_config.get('MAIL_USERNAME') and 
            mail_config.get('MAIL_PASSWORD') and
            mail_config.get('MAIL_USERNAME') != ''
        )
    
    def send_appointment_confirmation(self, senior_name, senior_email, appointment_date, 
                                       appointment_time, service_type, appointment_id,
                                       priority_score=None, is_emergency=False):
        """
        Send appointment confirmation email to senior after booking
        
        Args:
            senior_name (str): Full name of the senior
            senior_email (str): Email address of the senior
            appointment_date (str): Date of appointment (YYYY-MM-DD)
            appointment_time (str): Time of appointment (HH:MM)
            service_type (str): Type of health service
            appointment_id (int): ID of the appointment
            priority_score (int): AI priority score (optional)
            is_emergency (bool): Whether this is an emergency case
        
        Returns:
            tuple: (success, message)
        """
        if not self.is_configured:
            print(f"⚠️ Email not configured. Would send to {senior_email}")
            print(f"   To enable emails, set MAIL_USERNAME and MAIL_PASSWORD in .env file")
            return False, "Email service not configured"
        
        # Format date nicely
        try:
            formatted_date = datetime.strptime(appointment_date, '%Y-%m-%d').strftime('%B %d, %Y')
        except:
            formatted_date = appointment_date
        
        # Format time nicely
        try:
            formatted_time = datetime.strptime(appointment_time, '%H:%M').strftime('%I:%M %p')
        except:
            formatted_time = appointment_time
        
        # Determine priority message
        priority_message = self._get_priority_message(priority_score, is_emergency)
        
        subject = f"Appointment Confirmation - Barangay Sto. Niño Health Center"
        
        # Create HTML email body
        html_body = self._create_confirmation_email_html(
            senior_name=senior_name,
            appointment_date=formatted_date,
            appointment_time=formatted_time,
            service_type=service_type,
            appointment_id=appointment_id,
            priority_message=priority_message,
            is_emergency=is_emergency
        )
        
        # Create plain text version
        text_body = self._create_confirmation_email_text(
            senior_name=senior_name,
            appointment_date=formatted_date,
            appointment_time=formatted_time,
            service_type=service_type,
            appointment_id=appointment_id,
            priority_message=priority_message,
            is_emergency=is_emergency
        )
        
        # Send email asynchronously
        return self._send_email_async(senior_email, subject, html_body, text_body)
    
    def _get_priority_message(self, priority_score, is_emergency):
        """Generate user-friendly priority message"""
        if is_emergency:
            return {
                'level': 'URGENT',
                'color': '#dc3545',
                'message': '⚠️ EMERGENCY CASE - You will be prioritized. Please proceed to the health center immediately.'
            }
        elif priority_score and priority_score >= 200:
            return {
                'level': 'HIGH',
                'color': '#fd7e14',
                'message': '🔴 High Priority - Due to your age and health conditions, you have been given priority status.'
            }
        elif priority_score and priority_score >= 100:
            return {
                'level': 'MEDIUM',
                'color': '#ffc107',
                'message': '🟡 Medium Priority - Your appointment has been prioritized based on your profile.'
            }
        else:
            return {
                'level': 'NORMAL',
                'color': '#28a745',
                'message': '🟢 Normal Priority - We will attend to you in order of arrival.'
            }

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
    
    def _create_confirmation_email_html(self, senior_name, appointment_date, appointment_time,
                                          service_type, appointment_id, priority_message, is_emergency):
        """Create HTML version of the confirmation email"""
        
        emergency_class = "emergency-warning" if is_emergency else ""
        emergency_border = "border-left: 4px solid #dc3545;" if is_emergency else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Confirmation</title>
            <style>
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f5f7fa;
                    padding: 20px;
                }}
                .email-card {{
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .email-header {{
                    background: linear-gradient(135deg, #2c7da0, #1a5d7a);
                    color: white;
                    padding: 25px 20px;
                    text-align: center;
                }}
                .email-header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .email-header p {{
                    margin: 8px 0 0;
                    opacity: 0.9;
                }}
                .email-body {{
                    padding: 25px;
                }}
                .appointment-details {{
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 15px 0;
                    {emergency_border}
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #2c7da0;
                }}
                .priority-badge {{
                    display: inline-block;
                    background: {priority_message['color']};
                    color: {'#333' if priority_message['level'] == 'MEDIUM' else 'white'};
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .emergency-warning {{
                    background: #fff3cd;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .reminder-box {{
                    background: #e3f2fd;
                    border-radius: 12px;
                    padding: 15px 20px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    font-size: 12px;
                    color: #999;
                    border-top: 1px solid #e0e0e0;
                }}
                .btn {{
                    display: inline-block;
                    background: #2c7da0;
                    color: white;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 25px;
                    margin-top: 15px;
                }}
                @media (max-width: 480px) {{
                    .email-container {{
                        padding: 10px;
                    }}
                    .detail-row {{
                        flex-direction: column;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-card">
                    <div class="email-header">
                        <img src="cid:logo" alt="Barangay Sto. Niño" style="width:120px; display:block; margin:0 auto 10px;" />
                        <h1>🏥 Barangay Sto. Niño</h1>
                        <p>Health Center - Senior e-Health System</p>
                    </div>
                    
                    <div class="email-body">
                        <h2 style="color: #2c7da0; margin-top: 0;">Hello, {senior_name}!</h2>
                        
                        <p>Your health appointment has been successfully booked with our AI-Enhanced e-Health System.</p>
                        
                        <div class="appointment-details">
                            <h3 style="margin-top: 0; color: #333;">📋 Appointment Details</h3>
                            
                            <div class="detail-row">
                                <span class="detail-label">🏥 Service:</span>
                                <span><strong>{service_type}</strong></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">📅 Date:</span>
                                <span><strong>{appointment_date}</strong></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">⏰ Time:</span>
                                <span><strong>{appointment_time}</strong></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">🔢 Reference #:</span>
                                <span><strong>APT-{appointment_id:06d}</strong></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">⚡ Priority:</span>
                                <span>
                                    <span class="priority-badge">{priority_message['level']} PRIORITY</span>
                                </span>
                            </div>
                        </div>
                        
                        <div class="priority-message" style="margin: 15px 0; padding: 10px; background: #f0f7fa; border-radius: 8px;">
                            <p style="margin: 0;">{priority_message['message']}</p>
                        </div>
                        
                        <div class="reminder-box">
                            <strong>📌 Important Reminders:</strong>
                            <ul style="margin: 10px 0 0 20px; padding: 0;">
                                <li>Please arrive 15 minutes before your scheduled time</li>
                                <li>Bring your Senior Citizen ID and any medical records</li>
                                <li>Bring your current medications if applicable</li>
                                <li>Your appointment is subject to admin approval - we will notify you via email once confirmed</li>
                            </ul>
                        </div>
                        
                        <p><strong>What's next?</strong></p>
                        <ol>
                            <li>Our health center admin will review your appointment</li>
                            <li>You will receive another email when your appointment is approved</li>
                            <li>Once approved, you will receive your queue number</li>
                            <li>You can check your queue status anytime via your dashboard</li>
                        </ol>
                        
                        <div style="text-align: center;">
                            <a href="#" style="display: inline-block; background: #2c7da0; color: white; text-decoration: none; padding: 12px 25px; border-radius: 25px; margin-top: 10px;">
                                📱 Check Your Dashboard
                            </a>
                        </div>
                        
                        <hr style="margin: 25px 0 15px; border: none; border-top: 1px solid #e0e0e0;">
                        
                        <p style="font-size: 14px; color: #666;">
                            📍 <strong>Health Center Location:</strong> Barangay Sto. Niño Hall, [Street Name], [City/Municipality]<br>
                            📞 <strong>Contact Number:</strong> (02) 1234-5678<br>
                            📧 <strong>Email:</strong> healthcenter@barangaystoinino.gov.ph
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated message from Barangay Sto. Niño AI e-Health System.</p>
                        <p>© 2024 Barangay Sto. Niño. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_confirmation_email_text(self, senior_name, appointment_date, appointment_time,
                                         service_type, appointment_id, priority_message, is_emergency):
        """Create plain text version of the confirmation email"""
        
        return f"""
BARANGAY STO. NIÑO HEALTH CENTER
================================

Dear {senior_name},

Your health appointment has been successfully booked!

APPOINTMENT DETAILS:
-------------------
Service: {service_type}
Date: {appointment_date}
Time: {appointment_time}
Reference #: APT-{appointment_id:06d}
Priority: {priority_message['level']}

{priority_message['message']}

IMPORTANT REMINDERS:
-------------------
• Please arrive 15 minutes before your scheduled time
• Bring your Senior Citizen ID and medical records
• Bring your current medications if applicable
• Your appointment requires admin approval

WHAT'S NEXT?
-----------
1. Admin will review your appointment
2. You'll receive email confirmation when approved
3. Once approved, you'll get your queue number
4. Check queue status via your dashboard

Health Center Location: Barangay Sto. Niño Hall
Contact: (02) 1234-5678

This is an automated message. Please do not reply to this email.

Barangay Sto. Niño Health Center - Serving Our Seniors with Care
        """
    
    def _send_email_async(self, to_email, subject, html_body, text_body):
        """
        Send email asynchronously to prevent blocking the application
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_body (str): HTML version of email body
            text_body (str): Plain text version of email body
        """
        thread = threading.Thread(
            target=self._send_email_sync,
            args=(to_email, subject, html_body, text_body)
        )
        thread.daemon = True
        thread.start()
        return True, "Email queued for sending"
    
    def _send_email_sync(self, to_email, subject, html_body, text_body):
        """
        Actually send the email (called from thread)
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_body (str): HTML version of email body
            text_body (str): Plain text version of email body
        """
        if not self.is_configured:
            print(f"⚠️ Email not configured. Skipping email to {to_email}")
            return False
        
        try:
            # Build multipart/related message with multipart/alternative inside
            msg = MIMEMultipart('related')
            msg['From'] = self.mail_config['MAIL_USERNAME']
            msg['To'] = to_email
            msg['Subject'] = subject

            alt = MIMEMultipart('alternative')
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            alt.attach(text_part)
            alt.attach(html_part)

            msg.attach(alt)

            # Attach logo image if available (inline) - referenced in HTML with cid:logo
            try:
                logo_path = self._find_logo_path()
                if logo_path:
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

            # Send email
            server = smtplib.SMTP(
                self.mail_config['MAIL_SERVER'], 
                self.mail_config['MAIL_PORT']
            )
            server.starttls()
            server.login(
                self.mail_config['MAIL_USERNAME'], 
                self.mail_config['MAIL_PASSWORD']
            )
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Appointment confirmation email sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False


# Testing function - can be used to verify email configuration
def test_email_configuration(mail_config):
    """
    Test if email configuration is working
    
    Args:
        mail_config (dict): Email configuration
    
    Returns:
        tuple: (success, message)
    """
    test_email = EmailNotification(mail_config)
    
    if not test_email.is_configured:
        return False, "Email not configured. Please set MAIL_USERNAME and MAIL_PASSWORD in .env file"
    
    return True, "Email configuration looks good!"