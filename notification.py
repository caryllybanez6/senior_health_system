import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import threading
import os

class NotificationSystem:
    """Handles email and system notifications"""
    
    def __init__(self, mail_config):
        self.mail_config = mail_config

    def _find_logo_path(self):
        """Return the first existing logo path from supported file names."""
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

    def _get_logo_img_tag(self):
        """Return the logo tag referencing the CID inline image if the file exists."""
        if self._find_logo_path():
            return '<img src="cid:logo" alt="Barangay Sto. Niño" style="width:120px; display:block; margin:0 auto 10px;" />'
        return ''

    def send_email_async(self, to_email, subject, body):
        """Send email asynchronously para hindi bumagal ang app"""
        thread = threading.Thread(target=self._send_email, args=(to_email, subject, body))
        thread.daemon = True
        thread.start()
    
    def _send_email(self, to_email, subject, body):
        """Actual email sending"""
        if not self.mail_config.get('MAIL_USERNAME') or not self.mail_config.get('MAIL_PASSWORD'):
            print(f"Email not configured. Would send to {to_email}: {subject}")
            return False, "Email disabled (no config)"
        
        try:
            # Build a multipart/related message with multipart/alternative inside
            msg = MIMEMultipart('related')
            msg['From'] = self.mail_config['MAIL_USERNAME']
            msg['To'] = to_email
            msg['Subject'] = subject

            # Create the alternative part (plain + html)
            alt = MIMEMultipart('alternative')
            text_body = body.replace('<br>', '\n').replace('</p>', '\n').replace('<p>', '').replace('<h2>', '').replace('</h2>', '').replace('<strong>', '').replace('</strong>', '')
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(body, 'html')
            alt.attach(text_part)
            alt.attach(html_part)

            # Attach alternative into the related container
            msg.attach(alt)

            # Attach logo image if available and the HTML references cid:logo
            if 'cid:logo' in body:
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
            
            server = smtplib.SMTP(self.mail_config['MAIL_SERVER'], self.mail_config['MAIL_PORT'])
            server.starttls()
            server.login(self.mail_config['MAIL_USERNAME'], self.mail_config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True, "Email sent successfully"
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False, str(e)
    
    def send_appointment_reminder(self, senior_name, senior_email, appointment_date, 
                                   appointment_time, service_type):
        """Send appointment reminder email - mas natural ang dating"""
        subject = f"Reminder: Your {service_type} Appointment at Barangay Sto. Niño Health Center"
        logo_img = self._get_logo_img_tag()
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 550px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="text-align: center; padding-bottom: 15px; border-bottom: 2px solid #2c7da0;">
                    {logo_img}
                    <h2 style="color: #2c7da0; margin: 0;">Barangay Sto. Niño</h2>
                    <p style="margin: 5px 0 0; color: #666;">Health Center</p>
                </div>
                
                <div style="padding: 20px 0;">
                    <p style="font-size: 16px;">Dear <strong>{senior_name}</strong>,</p>
                    <p>This is to remind you about your scheduled health appointment:</p>
                    
                    <table style="width: 100%; margin: 15px 0; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0;"><strong>🏥 Service:</strong></td>
                            <td style="padding: 8px 0;">{service_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>📅 Date:</strong></td>
                            <td style="padding: 8px 0;">{appointment_date}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>⏰ Time:</strong></td>
                            <td style="padding: 8px 0;">{appointment_time}</td>
                        </tr>
                    </table>
                    
                    <div style="background: #f0f7fa; padding: 12px; border-radius: 8px; margin: 15px 0;">
                        <p style="margin: 0 0 5px;"><strong>📌 Reminders:</strong></p>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Please arrive 15 minutes before your schedule</li>
                            <li>Bring your Senior Citizen ID</li>
                            <li>Bring any current medications or medical records</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 15px;">
                        📍 <strong>Location:</strong> Barangay Sto. Niño Health Center<br>
                        📞 <strong>Contact:</strong> (02) 1234-5678
                    </p>
                </div>
                
                <div style="text-align: center; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999;">
                    <p>Barangay Sto. Niño Health Center - Serving Our Seniors with Care</p>
                </div>
            </div>
        </body>
        </html>
        """
        self.send_email_async(senior_email, subject, body)
        return True, "Email queued"
    
    def send_appointment_approved(self, senior_name, senior_email, queue_number, priority_level,
                                  appointment_date=None, appointment_time=None, service_type=None):
        """Send appointment approval notification with appointment details."""
        subject = "Your Appointment has been Confirmed - Barangay Sto. Niño Health Center"

        # Simplify priority level display - huwag masyadong technical
        friendly_priority = self._get_friendly_priority(priority_level)

        date_text = appointment_date or 'TBD'
        time_text = appointment_time or 'TBD'
        service_text = service_type or 'the requested service'

        logo_img = self._get_logo_img_tag()
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="text-align: center; padding-bottom: 15px; border-bottom: 2px solid #28a745;">
                    {logo_img}
                    <h2 style="color: #28a745; margin: 0;">✓ Appointment Confirmed</h2>
                </div>

                <div style="padding: 20px 0;">
                    <p style="font-size: 16px;">Dear <strong>{senior_name}</strong>,</p>
                    <p>Your appointment for <strong>{service_text}</strong> has been <strong style="color:#28a745;">approved</strong> by the health center.</p>

                    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <p style="margin: 0 0 8px;"><strong>Appointment Details</strong></p>
                        <p style="margin: 0;">📅 Date: {date_text} &nbsp; | &nbsp; ⏰ Time: {time_text}</p>
                        <p style="margin: 8px 0 0; font-size: 18px; font-weight: bold; color: #2c7da0;">Queue No: {queue_number}</p>
                        <p style="margin: 5px 0 0; color: #555;">{friendly_priority}</p>
                    </div>

                    <p><strong>What's next?</strong></p>
                    <ul>
                        <li>Please arrive 15 minutes before your scheduled time and bring your Senior Citizen ID.</li>
                        <li>We will notify you by email when your queue number is near.</li>
                        <li>If you need to cancel or reschedule, please contact the health center.</li>
                    </ul>
                </div>

                <div style="text-align: center; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999;">
                    <p>Barangay Sto. Niño Health Center - Serving Our Seniors with Care</p>
                </div>
            </div>
        </body>
        </html>
        """
        self.send_email_async(senior_email, subject, body)
        return True, "Email queued"
    
    def send_queue_update(self, senior_name, senior_email, queue_number, estimated_wait_time, priority_level):
        """Send queue status update"""
        subject = "Queue Update - Barangay Sto. Niño Health Center"
        friendly_priority = self._get_friendly_priority(priority_level)
        
        logo_img = self._get_logo_img_tag()
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 550px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <div style="text-align: center; padding-bottom: 15px; border-bottom: 2px solid #ffc107;">
                    {logo_img}
                    <h2 style="color: #e67e22; margin: 0;">Queue Status Update</h2>
                </div>
                
                <div style="padding: 20px 0;">
                    <p>Dear <strong>{senior_name}</strong>,</p>
                    <p>Here's your current queue status:</p>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; text-align: center; margin: 15px 0;">
                        <p style="margin: 0 0 5px;">Your Queue Number:</p>
                        <p style="font-size: 32px; font-weight: bold; color: #e67e22; margin: 5px 0;">{queue_number}</p>
                        <p style="margin: 10px 0 0;">Estimated wait time: <strong>{estimated_wait_time} minutes</strong></p>
                    </div>
                    
                    <p>{friendly_priority}</p>
                    <p>Please monitor your queue number. We will notify you when it's your turn.</p>
                </div>
                
                <div style="text-align: center; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999;">
                    <p>Barangay Sto. Niño Health Center - Serving Our Seniors with Care</p>
                </div>
            </div>
        </body>
        </html>
        """
        self.send_email_async(senior_email, subject, body)
        return True, "Email queued"
    
    def _get_friendly_priority(self, priority_level):
        """Convert technical priority to friendly message"""
        if 'CRITICAL' in priority_level:
            return "⚠️ For your safety, please proceed to the health center as soon as possible."
        elif 'HIGH' in priority_level:
            return "Your appointment has been prioritized. Estimated wait time is shorter."
        elif 'MEDIUM' in priority_level:
            return "You are in the regular queue. We will attend to you as soon as possible."
        else:
            return "We will notify you when it's your turn. Thank you for your patience."
    
    @staticmethod
    def detect_schedule_conflict(existing_appointments, new_date, new_time):
        """Detect schedule conflicts"""
        for app in existing_appointments:
            if str(app['appointment_date']) == new_date and str(app['appointment_time']) == new_time:
                return True, f"You already have an appointment scheduled at {new_time}. Please choose a different time."
        return False, None