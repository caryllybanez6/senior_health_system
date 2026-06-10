from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail
from flask_cors import CORS
from functools import wraps
import bcrypt
from datetime import datetime
import os
from dotenv import load_dotenv

# ITO ANG TAMANG IMPORT - WALANG "utils."
from config import DB_CONFIG, MAIL_CONFIG, SECRET_KEY
from ai_priority import AIPriorityScorer
from notification import NotificationSystem
from db import Database
import api
import init_db
# NEW IMPORT FOR EMAIL NOTIFICATION
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import threading
import os

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = SECRET_KEY
CORS(app)
app.register_blueprint(api.api_bp)

# Email configuration
app.config.update(MAIL_CONFIG)
mail = Mail(app)

# Initialize notification system
notification = NotificationSystem(MAIL_CONFIG)

# Ensure database, tables, and default admin exist before handling requests
database_initialized = False

@app.before_request
def initialize_database():
    global database_initialized
    if database_initialized:
        return
    try:
        init_db.create_database_and_tables()
        database_initialized = True
    except Exception as e:
        print(f"⚠️ Failed to initialize database: {e}")

# ========== NEW: EMAIL NOTIFICATION CLASS (Integrated) ==========
class AppointmentEmailNotifier:
    """
    Separate email notification system for appointment confirmations
    Sends email to senior IMMEDIATELY after booking
    """
    
    def __init__(self, mail_config):
        self.mail_config = mail_config
        self.is_configured = bool(
            mail_config.get('MAIL_USERNAME') and 
            mail_config.get('MAIL_PASSWORD') and
            mail_config.get('MAIL_USERNAME') != ''
        )
    
    def send_appointment_confirmation(self, senior_name, senior_email, appointment_date, 
                                       appointment_time, service_type, appointment_id,
                                       priority_score=None, is_emergency=False):
        """Send appointment confirmation email to senior after booking"""
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
                @media (max-width: 480px) {{
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
                        
                        <div style="margin: 15px 0; padding: 10px; background: #f0f7fa; border-radius: 8px;">
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
                        
                        <hr style="margin: 25px 0 15px; border: none; border-top: 1px solid #e0e0e0;">
                        
                        <p style="font-size: 14px; color: #666;">
                            📍 <strong>Health Center Location:</strong> Barangay Sto. Niño Hall<br>
                            📞 <strong>Contact Number:</strong> (02) 1234-5678
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
        """Send email asynchronously to prevent blocking"""
        thread = threading.Thread(
            target=self._send_email_sync,
            args=(to_email, subject, html_body, text_body)
        )
        thread.daemon = True
        thread.start()
        return True, "Email queued for sending"
    
    def _send_email_sync(self, to_email, subject, html_body, text_body):
        """Actually send the email (called from thread)"""
        if not self.is_configured:
            print(f"⚠️ Email not configured. Skipping email to {to_email}")
            return False
        
        try:
            # Build multipart/related with multipart/alternative inside so inline images render
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

# Initialize the appointment email notifier
appointment_email = AppointmentEmailNotifier(MAIL_CONFIG)

# ========== END OF EMAIL NOTIFICATION INTEGRATION ==========

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin':
            return redirect(url_for('senior_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def serialize_db_value(value):
    """Convert database values to JSON-safe types."""
    from datetime import date, datetime, time, timedelta
    from decimal import Decimal

    if isinstance(value, dict):
        return {k: serialize_db_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_db_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime('%H:%M:%S')
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value

@app.route('/', methods=['GET', 'POST'])
def index():
    # If already logged in, send to appropriate dashboard
    if 'user_id' in session:
        if session.get('user_type') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('senior_dashboard'))

    # Accept login POST from homepage login form
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # allow form to indicate user_type (if present on homepage form)
        form_user_type = request.form.get('user_type')

        # Check admin first (keeps previous behavior)
        admin = Database.execute_query(
            "SELECT * FROM admin WHERE username = %s",
            (username,),
            fetch_one=True
        )
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
            session['user_id'] = admin['id']
            session['user_name'] = admin['full_name']
            session['user_type'] = 'admin'
            return redirect(url_for('admin_dashboard'))

        # Check seniors
        senior = Database.execute_query(
            "SELECT * FROM seniors WHERE username = %s",
            (username,),
            fetch_one=True
        )
        if senior and bcrypt.checkpw(password.encode('utf-8'), senior['password_hash'].encode('utf-8')):
            session['user_id'] = senior['id']
            session['user_name'] = senior['full_name']
            session['user_type'] = 'senior'
            return redirect(url_for('senior_dashboard'))

        # If no match, render homepage with error
        return render_template('index.html', error='Invalid username or password')

    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login is handled on the homepage now.
    if request.method == 'POST':
        return index()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        age = int(request.form['age'])
        birthdate = request.form['birthdate']
        gender = request.form['gender']
        address = request.form['address']
        contact_number = request.form['contact_number']
        email = request.form['email']
        senior_id_number = request.form['senior_id_number']
        username = request.form['username']
        password = request.form['password']
        emergency_contact = request.form.get('emergency_contact', '')
        medical_conditions = request.form.get('medical_conditions', '')
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        result = Database.execute_query("""
            INSERT INTO seniors (full_name, age, birthdate, gender, address, contact_number, 
                               email, senior_id_number, username, password_hash, 
                               emergency_contact, medical_conditions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, age, birthdate, gender, address, contact_number, 
              email, senior_id_number, username, password_hash, 
              emergency_contact, medical_conditions))
        
        if result is not None:
            return redirect(url_for('login', registered=True))
        else:
            return render_template('register.html', error="Username, Email, or Senior ID already exists")
    
    return render_template('register.html')

@app.route('/senior/dashboard')
@login_required
def senior_dashboard():
    if session['user_type'] != 'senior':
        return redirect(url_for('login'))
    
    senior = Database.execute_query("SELECT * FROM seniors WHERE id = %s", (session['user_id'],), fetch_one=True)
    
    # Active appointments (pending only)
    active_appointments = Database.execute_query("""
        SELECT a.*, q.queue_number, q.priority_score, q.estimated_wait_time
        FROM appointments a
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.senior_id = %s AND a.status = 'pending'
        ORDER BY a.appointment_date ASC
    """, (session['user_id'],), fetch_all=True) or []
    
    # Appointment history (approved, completed, cancelled, rejected)
    appointment_history = Database.execute_query("""
        SELECT a.*, q.queue_number, q.priority_score, q.estimated_wait_time
        FROM appointments a
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.senior_id = %s AND a.status IN ('approved', 'completed', 'cancelled', 'rejected')
        ORDER BY a.appointment_date DESC
    """, (session['user_id'],), fetch_all=True) or []
    
    notifications = Database.execute_query("""
        SELECT * FROM notifications WHERE senior_id = %s ORDER BY created_at DESC LIMIT 10
    """, (session['user_id'],), fetch_all=True) or []

    services = Database.execute_query(
        "SELECT * FROM health_services WHERE is_active = TRUE",
        fetch_all=True
    ) or []
    
    return render_template('senior_dashboard.html', 
                          senior=senior, 
                          active_appointments=active_appointments,
                          appointment_history=appointment_history,
                          notifications=notifications,
                          services=services)

# ========== NEW: APPOINTMENT HISTORY ROUTE ==========
@app.route('/senior/history')
@login_required
def senior_history():
    if session['user_type'] != 'senior':
        return redirect(url_for('login'))
    
    appointment_history = Database.execute_query("""
        SELECT a.*, q.queue_number, q.priority_score
        FROM appointments a
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.senior_id = %s AND a.status IN ('completed', 'cancelled', 'rejected')
        ORDER BY a.appointment_date DESC
    """, (session['user_id'],), fetch_all=True) or []
    
    return render_template('appointment_history.html', appointment_history=appointment_history)

@app.route('/api/senior/appointments', methods=['GET'])
@login_required
def get_senior_appointments():
    """API endpoint to refresh appointment data"""
    import json
    from datetime import datetime
    
    if session['user_type'] != 'senior':
        return {'error': 'Unauthorized'}, 401
    
    # Active appointments
    active = Database.execute_query("""
        SELECT a.*, q.queue_number, q.priority_score, q.estimated_wait_time
        FROM appointments a
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.senior_id = %s AND a.status = 'pending'
        ORDER BY a.appointment_date ASC
    """, (session['user_id'],), fetch_all=True) or []
    
    # Appointment history
    history = Database.execute_query("""
        SELECT a.*, q.queue_number, q.priority_score, q.estimated_wait_time
        FROM appointments a
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.senior_id = %s AND a.status IN ('approved', 'completed', 'cancelled', 'rejected')
        ORDER BY a.appointment_date DESC
    """, (session['user_id'],), fetch_all=True) or []
    
    # Notifications
    notifs = Database.execute_query("""
        SELECT * FROM notifications WHERE senior_id = %s ORDER BY created_at DESC LIMIT 10
    """, (session['user_id'],), fetch_all=True) or []

    active = [serialize_db_value(item) for item in active]
    history = [serialize_db_value(item) for item in history]
    notifs = [serialize_db_value(item) for item in notifs]
    
    return {
        'success': True,
        'active_appointments': len(active),
        'active_appointments_list': active,
        'appointment_history': history,
        'notifications': notifs,
        'updated_at': datetime.now().isoformat()
    }

@app.route('/senior/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if session['user_type'] != 'senior':
        return redirect(url_for('login'))
    
    services = Database.execute_query(
        "SELECT * FROM health_services WHERE is_active = TRUE",
        fetch_all=True
    ) or []

    senior = Database.execute_query(
        "SELECT full_name, senior_id_number FROM seniors WHERE id = %s",
        (session['user_id'],),
        fetch_one=True
    )
    
    if request.method == 'POST':
        service_type = request.form['service_type']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        symptoms = request.form.get('symptoms', '')
        is_emergency = request.form.get('is_emergency') == 'on'

        existing = Database.execute_query("""
            SELECT appointment_date, appointment_time FROM appointments 
            WHERE senior_id = %s AND status IN ('pending', 'approved')
        """, (session['user_id'],), fetch_all=True) or []
        
        has_conflict, msg = NotificationSystem.detect_schedule_conflict(
            existing, appointment_date, appointment_time
        )
        
        if has_conflict:
            return render_template('book_appointment.html', 
                                 services=services, 
                                 senior=senior,
                                 error=msg)
        
        appointment_id, priority_score, error_response, status_code = api._book_appointment({
            'service_type': service_type,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'symptoms': symptoms,
            'is_emergency': is_emergency,
        })

        if error_response is not None:
            error_message = None
            try:
                error_message = error_response.get_json().get('error')
            except Exception:
                error_message = 'Unable to book appointment.'
            return render_template('book_appointment.html', services=services, senior=senior, error=error_message)

        if appointment_id:
            # Get senior info (again for email)
            senior_info = Database.execute_query(
                "SELECT email, full_name FROM seniors WHERE id = %s",
                (session['user_id'],),
                fetch_one=True
            )
            
            # ========== SEND EMAIL CONFIRMATION AFTER BOOKING ==========
            # This sends an email to the senior right after they book
            email_sent, email_message = appointment_email.send_appointment_confirmation(
                senior_name=senior_info['full_name'],
                senior_email=senior_info['email'],
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                service_type=service_type,
                appointment_id=appointment_id,
                priority_score=priority_score,
                is_emergency=is_emergency
            )
            print(f"📧 Appointment email send status: {email_sent} - {email_message}")
            # ========== END OF EMAIL NOTIFICATION ==========
            
            # Send reminder (existing system)
            notification.send_appointment_reminder(
                senior_info['full_name'],
                senior_info['email'],
                appointment_date,
                appointment_time,
                service_type
            )
            
            Database.execute_query("""
                INSERT INTO notifications (senior_id, title, message, type, sent_via)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['user_id'], 'Appointment Booked', 
                  f'Your {service_type} appointment has been booked for {appointment_date} at {appointment_time}. Please wait for admin approval.',
                  'appointment', 'system'))
            
            return redirect(url_for('queue_status', appointment_id=appointment_id))
    
    return render_template('book_appointment.html', services=services, senior=senior)

@app.route('/senior/queue/<int:appointment_id>')
@login_required
def queue_status(appointment_id):
    if session['user_type'] != 'senior':
        return redirect(url_for('login'))
    
    queue_info = Database.execute_query("""
        SELECT a.*, q.queue_number, q.priority_score, q.estimated_wait_time, 
               q.status as queue_status, q.position
        FROM appointments a
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.id = %s AND a.senior_id = %s
    """, (appointment_id, session['user_id']), fetch_one=True)
    
    if queue_info:
        queue_info['priority_level'] = AIPriorityScorer.get_priority_level(queue_info.get('priority_score') or 0)
        queue_info['priority_color'] = AIPriorityScorer.get_priority_color(queue_info.get('priority_score') or 0)
    
    return render_template('queue_status.html', queue=queue_info)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_seniors = Database.execute_query("SELECT COUNT(*) as total FROM seniors", fetch_one=True)
    pending_appointments = Database.execute_query("SELECT COUNT(*) as total FROM appointments WHERE status = 'pending'", fetch_one=True)
    queue_count = Database.execute_query("SELECT COUNT(*) as total FROM queue WHERE status = 'waiting'", fetch_one=True)
    
    recent_appointments = Database.execute_query("""
        SELECT a.*, s.full_name as senior_name, s.age, s.contact_number,
               q.queue_number, q.priority_score
        FROM appointments a
        JOIN seniors s ON a.senior_id = s.id
        LEFT JOIN queue q ON a.id = q.appointment_id
        WHERE a.status IN ('pending', 'approved')
        ORDER BY a.priority_score DESC, a.appointment_date ASC
        LIMIT 10
    """, fetch_all=True) or []
    
    for app in recent_appointments:
        app['priority_level'] = AIPriorityScorer.get_priority_level(app.get('priority_score') or 0)
    
    return render_template('admin_dashboard.html', 
                          total_seniors=total_seniors['total'] if total_seniors else 0,
                          pending_appointments=pending_appointments['total'] if pending_appointments else 0,
                          queue_count=queue_count['total'] if queue_count else 0,
                          appointments=recent_appointments)

@app.route('/admin/appointments')
@admin_required
def admin_appointments():
    appointments = Database.execute_query("""
        SELECT a.*, s.full_name as senior_name, s.age, s.contact_number, s.email,
               s.medical_conditions
        FROM appointments a
        JOIN seniors s ON a.senior_id = s.id
        ORDER BY 
            CASE WHEN a.status = 'pending' THEN 0 ELSE 1 END,
            a.priority_score DESC,
            a.appointment_date ASC
    """, fetch_all=True) or []
    
    for app in appointments:
        if app['status'] == 'pending':
            new_score = AIPriorityScorer.calculate_total_priority(
                senior_age=app['age'],
                symptoms=app.get('symptoms', ''),
                is_emergency=app.get('is_emergency', False),
                waiting_minutes=0,
                medical_conditions=app.get('medical_conditions', '')
            )
            app['priority_score'] = new_score
        app['priority_level'] = AIPriorityScorer.get_priority_level(app.get('priority_score') or 0)
        app['priority_color'] = AIPriorityScorer.get_priority_color(app.get('priority_score') or 0)
    
    return render_template('admin/manage_appointments.html', appointments=appointments)

@app.route('/admin/queue')
@admin_required
def admin_queue():
    queue_items = Database.execute_query("""
        SELECT q.id AS queue_id, q.appointment_id, q.queue_number, q.priority_score,
               q.estimated_wait_time, q.status AS queue_status, q.position,
               a.service_type, a.appointment_date, a.appointment_time,
               s.full_name AS senior_name, s.age, s.contact_number, s.email
        FROM queue q
        JOIN appointments a ON q.appointment_id = a.id
        JOIN seniors s ON a.senior_id = s.id
        WHERE q.status IN ('waiting', 'in_progress')
        ORDER BY q.position ASC
    """, fetch_all=True) or []

    for item in queue_items:
        item['priority_level'] = AIPriorityScorer.get_priority_level(item.get('priority_score') or 0)
        item['priority_color'] = AIPriorityScorer.get_priority_color(item.get('priority_score') or 0)

    return render_template('admin/queue_management.html', queue_items=queue_items)

@app.route('/admin/queue/update/<int:queue_id>', methods=['POST'])
@admin_required
def update_queue_item(queue_id):
    action = request.form.get('action')
    if action not in {'start', 'complete', 'skip'}:
        return redirect(url_for('admin_queue'))

    status_map = {
        'start': 'in_progress',
        'complete': 'completed',
        'skip': 'skipped'
    }
    new_status = status_map[action]

    Database.execute_query("UPDATE queue SET status = %s WHERE id = %s", (new_status, queue_id))

    if action == 'complete':
        appointment = Database.execute_query(
            "SELECT appointment_id FROM queue WHERE id = %s", (queue_id,), fetch_one=True
        )
        if appointment and appointment.get('appointment_id'):
            Database.execute_query(
                "UPDATE appointments SET status = 'completed' WHERE id = %s",
                (appointment['appointment_id'],)
            )

    return redirect(url_for('admin_queue'))

@app.route('/admin/notifications')
@admin_required
def admin_notifications():
    notifications = Database.execute_query("""
        SELECT n.*, s.full_name as senior_name
        FROM notifications n
        LEFT JOIN seniors s ON n.senior_id = s.id
        ORDER BY n.created_at DESC
        LIMIT 50
    """, fetch_all=True) or []

    return render_template('admin/notifications.html', notifications=notifications)

@app.route('/admin/approve/<int:appointment_id>', methods=['POST'])
@admin_required
def approve_appointment(appointment_id):
    appointment = Database.execute_query("""
        SELECT a.*, s.full_name, s.email, s.age, s.medical_conditions
        FROM appointments a
        JOIN seniors s ON a.senior_id = s.id
        WHERE a.id = %s
    """, (appointment_id,), fetch_one=True)
    
    if not appointment:
        return redirect(url_for('admin_appointments'))
    
    Database.execute_query("UPDATE appointments SET status = 'approved' WHERE id = %s", (appointment_id,))
    
    other_appointments = Database.execute_query("""
        SELECT a.*, s.age, s.medical_conditions
        FROM appointments a
        JOIN seniors s ON a.senior_id = s.id
        WHERE a.status = 'approved' AND a.id != %s
    """, (appointment_id,), fetch_all=True) or []
    
    all_appointments = other_appointments + [appointment]
    appointments_list = []
    
    for app in all_appointments:
        appointments_list.append({
            'id': app['id'],
            'age': app['age'],
            'symptoms': app.get('symptoms', ''),
            'is_emergency': app.get('is_emergency', False),
            'medical_conditions': app.get('medical_conditions', ''),
            'waiting_minutes': 0
        })
    
    arranged_queue = AIPriorityScorer.arrange_queue(appointments_list)
    
    Database.execute_query("""
        DELETE q FROM queue q
        JOIN appointments a ON q.appointment_id = a.id
        WHERE a.status = 'approved'
    """)
    
    for item in arranged_queue:
        Database.execute_query("""
            INSERT INTO queue (appointment_id, queue_number, priority_score, 
                             estimated_wait_time, status, position)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (item['id'], item['queue_number'], item['priority_score'], 
              30, 'waiting', item['queue_position']))
    
    approved_item = next((item for item in arranged_queue if item['id'] == appointment_id), None)
    if approved_item:
        notification.send_appointment_approved(
            appointment['full_name'],
            appointment['email'],
            approved_item['queue_number'],
            AIPriorityScorer.get_priority_level(approved_item['priority_score']),
            appointment_date=appointment.get('appointment_date'),
            appointment_time=appointment.get('appointment_time'),
            service_type=appointment.get('service_type')
        )
        Database.execute_query("""
            INSERT INTO notifications (senior_id, title, message, type, sent_via)
            VALUES (%s, %s, %s, %s, %s)
        """, (appointment['senior_id'], 'Appointment Approved', 
              f'Your appointment has been approved. Queue number: {approved_item["queue_number"]}. Priority: {AIPriorityScorer.get_priority_level(approved_item["priority_score"])}',
              'appointment', 'email'))
    
    return redirect(url_for('admin_appointments'))

@app.route('/admin/reject/<int:appointment_id>', methods=['POST'])
@admin_required
def reject_appointment(appointment_id):
    appointment = Database.execute_query("""
        SELECT a.*, s.full_name, s.email
        FROM appointments a
        JOIN seniors s ON a.senior_id = s.id
        WHERE a.id = %s
    """, (appointment_id,), fetch_one=True)
    
    if appointment:
        Database.execute_query("UPDATE appointments SET status = 'rejected' WHERE id = %s", (appointment_id,))
        
        Database.execute_query("""
            INSERT INTO notifications (senior_id, title, message, type)
            VALUES (%s, %s, %s, %s)
        """, (appointment['senior_id'], 'Appointment Rejected', 
              f'Your appointment on {appointment["appointment_date"]} was rejected. Please book another schedule.',
              'appointment'))
    
    return redirect(url_for('admin_appointments'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    daily_reports = Database.execute_query("""
        SELECT DATE(appointment_date) as date, COUNT(*) as count
        FROM appointments
        WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(appointment_date)
        ORDER BY date DESC
    """, fetch_all=True) or []
    
    service_stats = Database.execute_query("""
        SELECT service_type, COUNT(*) as count
        FROM appointments
        GROUP BY service_type
        ORDER BY count DESC
    """, fetch_all=True) or []
    
    queue_stats = Database.execute_query("""
        SELECT AVG(priority_score) as avg_priority, COUNT(*) as total_processed
        FROM queue
        WHERE status = 'completed'
    """, fetch_one=True)
    
    age_distribution = Database.execute_query("""
        SELECT 
            CASE 
                WHEN age BETWEEN 60 AND 69 THEN '60-69'
                WHEN age BETWEEN 70 AND 79 THEN '70-79'
                WHEN age >= 80 THEN '80+'
            END as age_group,
            COUNT(*) as count
        FROM seniors
        GROUP BY age_group
    """, fetch_all=True) or []
    
    return render_template('admin/reports.html', 
                          daily_reports=daily_reports,
                          service_stats=service_stats,
                          queue_stats=queue_stats,
                          age_distribution=age_distribution)

@app.route('/admin/seniors')
@admin_required
def admin_seniors():
    seniors = Database.execute_query("""
        SELECT * FROM seniors ORDER BY created_at DESC
    """, fetch_all=True) or []
    
    return render_template('admin/manage_seniors.html', seniors=seniors)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AI-Enhanced e-Health System for Senior Citizens")
    print("="*60)
    port = int(os.environ.get('PORT', 5000))
    print(f"📍 Server running at port: {port}")
    print(f"🔑 Admin Login: username='admin', password='admin123'")
    print("\n📧 Email Notification Status:")
    if MAIL_CONFIG.get('MAIL_USERNAME') and MAIL_CONFIG.get('MAIL_PASSWORD'):
        print(f"   ✅ Email configured: {MAIL_CONFIG['MAIL_USERNAME']}")
    else:
        print("   ⚠️ Email NOT configured - add MAIL_USERNAME and MAIL_PASSWORD to .env")
    print("="*60 + "\n")
    is_production = os.environ.get('FLASK_ENV') == 'production'
    app.run(debug=not is_production, host='0.0.0.0', port=port)