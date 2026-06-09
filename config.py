import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'C@ryll025'),
    'database': os.getenv('MYSQL_DATABASE', 'senior_health_system')
}

# Email Configuration
MAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME', ''),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD', '')
}

# Application Config
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-this')