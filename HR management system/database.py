import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'abia'),
    'database': os.getenv('MYSQL_DATABASE', 'hr_management')
}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as err:
        print('Database connection error:', err)
        print('Connection settings:', DB_CONFIG)
        raise


def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS Interviews ('
            'id INT AUTO_INCREMENT PRIMARY KEY, '
            'application_id INT NOT NULL, '
            'interview_date DATE,'
            'interviewer VARCHAR(255), '
            'interview_status VARCHAR(100), '
            'notes TEXT '
            ')'
        )
        conn.commit()
    except Error as err:
        print('Database initialization error:', err)
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
