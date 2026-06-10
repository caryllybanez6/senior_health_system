import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Database URL support for Railway and other hosts
database_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL') or os.getenv('RAILWAY_DATABASE_URL') or os.getenv('RAILWAY_MYSQL_URL')

def _parse_database_url(url):
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/') if parsed.path else ''
    }

if database_url:
    DB_CONFIG = _parse_database_url(database_url)
else:
    DB_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'senior_health_system')
    }

# Email Configuration
MAIL_CONFIG = {
    'MAIL_SERVER': os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)),
    'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes'],
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME', ''),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD', '')
}

# Application Config
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())