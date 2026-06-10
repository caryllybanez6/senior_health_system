import mysql.connector
from mysql.connector import Error
import bcrypt
import os
from dotenv import load_dotenv
from config import DB_CONFIG

# Load environment variables from .env file
load_dotenv()

def create_database_and_tables():
    """Initialize MySQL database and create all tables"""

    try:
        db_name = DB_CONFIG.get('database') or os.getenv('MYSQL_DATABASE', 'senior_health_system')
        connection_params = {
            'host': DB_CONFIG.get('host', os.getenv('MYSQL_HOST', 'localhost')),
            'user': DB_CONFIG.get('user', os.getenv('MYSQL_USER', 'root')),
            'password': DB_CONFIG.get('password', os.getenv('MYSQL_PASSWORD', '')),
            'port': int(DB_CONFIG.get('port', os.getenv('MYSQL_PORT', 3306) or 3306))
        }

        # First try to connect using the configured database if it exists.
        try:
            connection = mysql.connector.connect(**{
                **connection_params,
                'database': db_name
            })
        except Error as e:
            # If the database does not yet exist, connect without it and create it.
            if getattr(e, 'errno', None) == 1049:
                connection = mysql.connector.connect(**connection_params)
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                cursor.execute(f"USE `{db_name}`")
            else:
                raise
        else:
            cursor = connection.cursor()

        # Create database if not exists when connected without a database
        if connection.database is None:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
            cursor.execute(f"USE `{db_name}`")

        # SQL schema definitions
        tables_sql = """
        CREATE TABLE IF NOT EXISTS seniors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            senior_id_number VARCHAR(50) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            age INT NOT NULL,
            birthdate DATE NOT NULL,
            gender ENUM('Male', 'Female', 'Other') NOT NULL,
            address TEXT NOT NULL,
            contact_number VARCHAR(20) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            emergency_contact VARCHAR(20),
            medical_conditions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            role VARCHAR(50) DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            senior_id INT NOT NULL,
            service_type VARCHAR(100) NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            priority_score INT DEFAULT 0,
            status ENUM('pending', 'approved', 'completed', 'cancelled', 'rejected') DEFAULT 'pending',
            symptoms TEXT,
            is_emergency BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (senior_id) REFERENCES seniors(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS queue (
            id INT AUTO_INCREMENT PRIMARY KEY,
            appointment_id INT NOT NULL,
            queue_number VARCHAR(20) NOT NULL,
            priority_score INT NOT NULL,
            estimated_wait_time INT DEFAULT 30,
            status ENUM('waiting', 'in_progress', 'completed', 'skipped') DEFAULT 'waiting',
            position INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            senior_id INT,
            admin_id INT,
            title VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            type ENUM('appointment', 'queue', 'reminder', 'announcement') DEFAULT 'announcement',
            is_read BOOLEAN DEFAULT FALSE,
            sent_via VARCHAR(50) DEFAULT 'email',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (senior_id) REFERENCES seniors(id) ON DELETE CASCADE,
            FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS health_services (
            id INT AUTO_INCREMENT PRIMARY KEY,
            service_name VARCHAR(100) NOT NULL,
            description TEXT,
            duration_minutes INT DEFAULT 30,
            is_active BOOLEAN DEFAULT TRUE
        );
        """

        # Execute each statement separately
        for statement in tables_sql.split(';'):
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Error as e:
                    print(f"❌ SQL Error: {e}")

        # Insert default admin (password: admin123)
        admin_password = bcrypt.hashpw(
            'admin123'.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute("""
            INSERT IGNORE INTO admin (username, email, password_hash, full_name) 
            VALUES ('admin', 'admin@healthsystem.com', %s, 'System Administrator')
        """, (admin_password,))

        # Insert default health services
        services = [
            ('General Check-up', 'Regular health check and vital signs monitoring', 30),
            ('Blood Pressure Monitoring', 'Blood pressure check and consultation', 20),
            ('Hypertension Management', 'Hypertension assessment, monitoring, and medication follow-up', 30),
            ('Medication Refill', 'Prescription medication refill', 15),
            ('Vaccination', 'Flu and other routine vaccinations', 20),
            ('Dental Check-up', 'Basic dental examination', 30),
            ('Eye Check-up', 'Vision screening', 25)
        ]

        for service in services:
            cursor.execute("""
                INSERT IGNORE INTO health_services (service_name, description, duration_minutes)
                VALUES (%s, %s, %s)
            """, service)

        connection.commit()
        print("✅ Database and tables created successfully!")
        print("✅ Default admin account created: username='admin', password='admin123'")

    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    create_database_and_tables()
