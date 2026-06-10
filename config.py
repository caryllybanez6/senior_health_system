import os
from dotenv import load_dotenv
from urllib.parse import parse_qs, urlparse

load_dotenv()

# Database URL support for Railway and other hosts
def _env_first(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _is_database_url(value):
    if not value or not isinstance(value, str):
        return False
    lower = value.strip().lower()
    if lower.startswith(('mysql://', 'mariadb://')):
        return True
    if 'password=' in lower and ('data source=' in lower or 'server=' in lower or 'host=' in lower or 'database=' in lower):
        return True
    return False


def _is_web_url(value):
    if not value or not isinstance(value, str):
        return False
    lower = value.strip().lower()
    if lower.startswith(('http://', 'https://')):
        return True
    return any(domain in lower for domain in (
        '.up.railway.app', 'railway.app', 'herokuapp.com', 'vercel.app',
        'fly.dev', 'netlify.app', 'azurewebsites.net'
    ))


def _is_db_env_name(name):
    if not name or not isinstance(name, str):
        return False
    lower_name = name.lower()
    if any(skip in lower_name for skip in ('static_url', 'public_domain', 'private_domain', 'hostname', 'deployment_id', 'service_id', 'git_branch', 'git_commit')):
        return False
    return any(token in lower_name for token in ('mysql', 'db', 'database', 'connstr', 'uri', 'url'))


def _find_database_url():
    # First, try specific database URL env vars
    candidates = [
        'DATABASE_URL', 'MYSQL_URL', 'MYSQL_DATABASE_URL',
        'RAILWAY_DATABASE_URL', 'RAILWAY_MYSQL_URL', 'RAILWAY_MYSQL',
        'DB_URL', 'DB_DATABASE_URL', 'MARIADB_URL',
        'MYSQLCONNSTR', 'MYSQLCONNSTR_localdb',
        'CLEARDB_DATABASE_URL', 'JAWSDB_URL'
    ]

    for name in candidates:
        value = os.getenv(name)
        if value and 'static_url' in name.lower():
            continue
        if _is_database_url(value) and not _is_web_url(value):
            return name, value

    # Look for generic database connection strings in env vars
    for name, value in os.environ.items():
        if not value:
            continue
        lower_name = name.lower()

        if 'static_url' in lower_name:
            continue
        if not _is_db_env_name(lower_name):
            continue

        if _is_web_url(value):
            continue

        if _is_database_url(value):
            return name, value

        if '://' in value and any(token in lower_name for token in ('mysql', 'mariadb', 'db', 'database')):
            return name, value

        if '=' in value and any(param in value.lower() for param in ('host=', 'user=', 'password=', 'database=', 'data source=')):
            return name, value

    return None, None


def _find_env_value(label_parts, required_parts=None, default=None):
    required_parts = required_parts or []
    for name, value in os.environ.items():
        lower_name = name.lower()
        if not value:
            continue
        if all(part in lower_name for part in label_parts) and all(req in lower_name for req in required_parts):
            return value
    return default


raw_database_url_name, raw_database_url = _find_database_url()

# EXPLICIT: Never use RAILWAY_STATIC_URL as database connection
if raw_database_url_name == 'RAILWAY_STATIC_URL' or raw_database_url_name == 'RAILWAY_PUBLIC_DOMAIN' or raw_database_url_name == 'RAILWAY_PRIVATE_DOMAIN':
    raw_database_url = None
    raw_database_url_name = None

# Validate that raw_database_url is actually a database connection, not a web URL
if raw_database_url:
    parsed = urlparse(raw_database_url)
    if _is_web_url(raw_database_url) or not ((parsed.scheme and parsed.username) or 'password=' in raw_database_url.lower() or ';' in raw_database_url):
        raw_database_url = None  # Reject web URLs or non-auth URLs


def _safe_int(value, default):
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _normalize_database_url(url):
    if not url:
        return url
    if url.startswith('jdbc:'):
        return url[len('jdbc:'):]
    return url


def _parse_mysqlconnstr(url):
    # Support Azure-style MySQL connection strings like:
    # "Database=db;Data Source=host;User Id=user;Password=pass;"
    parts = [part.strip() for part in url.split(';') if part.strip()]
    values = {}
    for part in parts:
        if '=' in part:
            key, val = part.split('=', 1)
            values[key.strip().lower()] = val.strip()

    return {
        'host': values.get('data source') or values.get('server') or values.get('host'),
        'user': values.get('user id') or values.get('uid') or values.get('username'),
        'password': values.get('password') or values.get('pwd'),
        'database': values.get('database') or values.get('db'),
        'port': _safe_int(values.get('port'), 3306)
    }


def _parse_database_url(url):
    normalized_url = _normalize_database_url(url)
    lower_url = normalized_url.lower()
    if 'database=' in lower_url and 'data source=' in lower_url:
        return _parse_mysqlconnstr(normalized_url)

    parsed = urlparse(normalized_url)
    
    host = parsed.hostname or os.getenv('MYSQL_HOST') or os.getenv('DB_HOST') or os.getenv('DATABASE_HOST') or 'localhost'
    user = parsed.username or os.getenv('MYSQL_USER') or os.getenv('DB_USER') or os.getenv('DATABASE_USER') or 'root'
    password = parsed.password or os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD') or os.getenv('DATABASE_PASSWORD') or ''
    
    database = parsed.path.lstrip('/') if parsed.path else ''
    if not database:
        query_params = parse_qs(parsed.query or '')
        database = query_params.get('database', query_params.get('db', query_params.get('dbname', [''])))[0] or ''
    if not database:
        database = os.getenv('MYSQL_DATABASE', os.getenv('DB_DATABASE', 'senior_health_system'))

    port = parsed.port or _safe_int(os.getenv('MYSQL_PORT', os.getenv('DB_PORT', 3306)), 3306)

    return {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': port
    }

if raw_database_url:
    DB_CONFIG = _parse_database_url(raw_database_url)
    DB_SOURCE = raw_database_url_name or 'raw_database_url'
else:
    host = _env_first(
        'RAILWAY_MYSQL_HOST', 'RAILWAY_HOST', 'RAILWAY_DB_HOST', 'RAILWAY_MYSQLHOST',
        'MYSQLHOST', 'MYSQL_HOST', 'DB_HOST', 'DATABASE_HOST', 'DBHOST',
        'DATABASE_SERVER', 'MYSQL_HOSTNAME', default=None
    ) or _find_env_value(['host'], ['mysql', 'db', 'railway'], default=None)

    user = _env_first(
        'RAILWAY_MYSQL_USER', 'RAILWAY_USER', 'RAILWAY_DB_USER',
        'MYSQLUSER', 'MYSQL_USER', 'DB_USER', 'DATABASE_USER', 'DATABASE_USERNAME',
        'DB_USERNAME', default=None
    ) or _find_env_value(['user'], ['mysql', 'db', 'railway'], default=None)

    password = _env_first(
        'RAILWAY_MYSQL_PASSWORD', 'RAILWAY_PASSWORD', 'RAILWAY_DB_PASSWORD',
        'MYSQLPASSWORD', 'MYSQL_PASSWORD', 'DB_PASSWORD', 'DATABASE_PASSWORD',
        default=None
    ) or _find_env_value(['password'], ['mysql', 'db', 'railway'], default=None)

    database = _env_first(
        'RAILWAY_MYSQL_DATABASE', 'RAILWAY_DATABASE', 'RAILWAY_DB_DATABASE',
        'MYSQLDATABASE', 'MYSQL_DATABASE', 'DB_DATABASE', 'DATABASE_NAME',
        'DB_NAME', default=None
    ) or _find_env_value(['database'], ['mysql', 'db', 'railway'], default=None)

    port = _safe_int(
        _env_first(
            'RAILWAY_MYSQL_PORT', 'RAILWAY_PORT', 'RAILWAY_DB_PORT',
            'MYSQLPORT', 'MYSQL_PORT', 'DB_PORT', 'DATABASE_PORT', default=None
        ) or _find_env_value(['port'], ['mysql', 'db', 'railway'], default=None),
        3306
    )

    db_env_present = any([
        raw_database_url,
        host, user, database,
        os.getenv('MYSQLHOST'), os.getenv('MYSQL_HOST'),
        os.getenv('MYSQLUSER'), os.getenv('MYSQL_USER'),
        os.getenv('MYSQLDATABASE'), os.getenv('MYSQL_DATABASE'),
        os.getenv('RAILWAY_MYSQL_HOST'), os.getenv('RAILWAY_MYSQL_USER'),
        os.getenv('RAILWAY_MYSQL_DATABASE'), os.getenv('RAILWAY_MYSQL_PORT'),
        os.getenv('RAILWAY_DATABASE_URL'), os.getenv('DATABASE_URL')
    ])

    if not db_env_present and os.getenv('RAILWAY_STATIC_URL'):
        DB_SOURCE = 'missing_db_env'
    else:
        DB_SOURCE = 'fallback_env_vars'

    DB_CONFIG = {
        'host': host or 'localhost',
        'user': user or 'root',
        'password': password or '',
        'database': database or 'senior_health_system',
        'port': port
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