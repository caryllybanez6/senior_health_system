import os
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG, DB_SOURCE, raw_database_url, raw_database_url_name

class Database:
    
    @staticmethod
    def get_connection():
        try:
            connection_params = {
                'host': DB_CONFIG.get('host', 'localhost'),
                'user': DB_CONFIG.get('user', 'root'),
                'password': DB_CONFIG.get('password', ''),
                'database': DB_CONFIG.get('database', ''),
                'autocommit': False
            }
            if DB_CONFIG.get('port'):
                connection_params['port'] = int(DB_CONFIG['port'])

            connection = mysql.connector.connect(**connection_params)
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            print(f"DB_SOURCE={DB_SOURCE}")
            print(f"RAW_DATABASE_URL_SOURCE={raw_database_url_name} raw_database_url={'SET' if raw_database_url else 'NONE'}")
            print(f"DB_CONFIG={DB_CONFIG}")
            print(f"Env MYSQL_HOST={os.getenv('MYSQL_HOST')} MYSQL_DATABASE={os.getenv('MYSQL_DATABASE')} MYSQL_USER={os.getenv('MYSQL_USER')} MYSQL_PASSWORD={'SET' if os.getenv('MYSQL_PASSWORD') else 'NONE'} MYSQL_PORT={os.getenv('MYSQL_PORT')}")
            print(f"Env MYSQLHOST={os.getenv('MYSQLHOST')} MYSQLUSER={os.getenv('MYSQLUSER')} MYSQLPASSWORD={'SET' if os.getenv('MYSQLPASSWORD') else 'NONE'} MYSQLPORT={os.getenv('MYSQLPORT')}")
            print(f"Env DB_HOST={os.getenv('DB_HOST')} DB_DATABASE={os.getenv('DB_DATABASE')} DB_USER={os.getenv('DB_USER')} DB_PASSWORD={'SET' if os.getenv('DB_PASSWORD') else 'NONE'} DB_PORT={os.getenv('DB_PORT')}")
            print(f"Env RAILWAY_HOST={os.getenv('RAILWAY_HOST')} RAILWAY_DATABASE={os.getenv('RAILWAY_DATABASE')} RAILWAY_USER={os.getenv('RAILWAY_USER')} RAILWAY_PASSWORD={'SET' if os.getenv('RAILWAY_PASSWORD') else 'NONE'} RAILWAY_PORT={os.getenv('RAILWAY_PORT')}")
            print(f"Env RAILWAY_MYSQL_HOST={os.getenv('RAILWAY_MYSQL_HOST')} RAILWAY_MYSQL_DATABASE={os.getenv('RAILWAY_MYSQL_DATABASE')} RAILWAY_MYSQL_USER={os.getenv('RAILWAY_MYSQL_USER')} RAILWAY_MYSQL_PASSWORD={'SET' if os.getenv('RAILWAY_MYSQL_PASSWORD') else 'NONE'} RAILWAY_MYSQL_PORT={os.getenv('RAILWAY_MYSQL_PORT')}")
            print(f"Env RAILWAY_STATIC_URL={os.getenv('RAILWAY_STATIC_URL')}")
            print(f"Env DATABASE_URL set={'yes' if os.getenv('DATABASE_URL') else 'no'}")
            print(f"Env RAILWAY_DATABASE_URL set={'yes' if os.getenv('RAILWAY_DATABASE_URL') else 'no'}")
            print(f"Env RAILWAY_MYSQL_URL set={'yes' if os.getenv('RAILWAY_MYSQL_URL') else 'no'}")
            return None

        if DB_SOURCE == 'missing_db_env':
            print('❌ Railway detected but no database credentials were found.')
            print('   Set Railway MySQL env vars or link a MySQL service.')
            print('   Required env vars: RAILWAY_MYSQL_HOST, RAILWAY_MYSQL_USER, RAILWAY_MYSQL_PASSWORD, RAILWAY_MYSQL_DATABASE, RAILWAY_MYSQL_PORT')
            return None
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=False):
        connection = None
        cursor = None
        result = None
        
        try:
            connection = Database.get_connection()
            if connection is None:
                return None
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid
            
            return result
            
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()