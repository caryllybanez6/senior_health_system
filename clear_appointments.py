import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


def clear_app_data():
    """Delete appointment, queue, health service, and notification records from the configured database."""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            autocommit=False
        )

        cursor = connection.cursor()
        print(f"Connecting to database: {DB_CONFIG['database']} on {DB_CONFIG['host']}")

        # Clear dependent appointment data only.
        cursor.execute("DELETE FROM queue")
        deleted_queue = cursor.rowcount

        cursor.execute("DELETE FROM notifications")
        deleted_notifications = cursor.rowcount

        cursor.execute("DELETE FROM appointments")
        deleted_appointments = cursor.rowcount

        connection.commit()
        print(f"✅ Cleared appointment-related data successfully.")
        print(f"   Queue rows removed: {deleted_queue}")
        print(f"   Appointment rows removed: {deleted_appointments}")
        print(f"   Notification rows removed: {deleted_notifications}")

    except Error as e:
        if connection and connection.is_connected():
            connection.rollback()
        print(f"❌ Database error while clearing app data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == '__main__':
    clear_app_data()
