import os
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG, DB_SOURCE  # <-- ITO ANG TAMA, WALANG "utils."

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
            print(f"DB_CONFIG host={DB_CONFIG.get('host')} user={DB_CONFIG.get('user')} database={DB_CONFIG.get('database')} port={DB_CONFIG.get('port')}")
            print(f"Env MYSQL_HOST={os.getenv('MYSQL_HOST')} MYSQL_DATABASE={os.getenv('MYSQL_DATABASE')} MYSQL_USER={os.getenv('MYSQL_USER')} MYSQL_PORT={os.getenv('MYSQL_PORT')}")
            print(f"Env DB_HOST={os.getenv('DB_HOST')} DB_DATABASE={os.getenv('DB_DATABASE')} DB_USER={os.getenv('DB_USER')} DB_PORT={os.getenv('DB_PORT')}")
            print(f"Env DATABASE_URL set={'yes' if os.getenv('DATABASE_URL') else 'no'}")
            print(f"Env RAILWAY_DATABASE_URL set={'yes' if os.getenv('RAILWAY_DATABASE_URL') else 'no'}")
            print(f"Env RAILWAY_MYSQL_URL set={'yes' if os.getenv('RAILWAY_MYSQL_URL') else 'no'}")
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