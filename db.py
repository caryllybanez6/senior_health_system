import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG  # <-- ITO ANG TAMA, WALANG "utils."

class Database:
    
    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                autocommit=False
            )
            return connection
        except Error as e:
            print(f"Error: {e}")
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