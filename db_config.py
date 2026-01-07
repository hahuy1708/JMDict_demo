# db_config.py
import mysql.connector
from dotenv import load_dotenv 
import os
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),       
    'password': os.getenv('DB_PASSWORD'),       
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT')),
    'charset': 'utf8mb4', 
    'collation': 'utf8mb4_unicode_ci'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
    CREATE TABLE IF NOT EXISTS dictionary (
        id VARCHAR(20) PRIMARY KEY,
        headword VARCHAR(100) NOT NULL,
        reading VARCHAR(100) NULL,
        is_common TINYINT(1) NOT NULL DEFAULT 0,
        gloss_text TEXT NOT NULL,
        raw_json JSON NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

        INDEX idx_headword (headword),
        INDEX idx_reading (reading),
        INDEX idx_common (is_common),
        FULLTEXT INDEX ft_gloss_text (gloss_text)
    ) ENGINE=InnoDB
      DEFAULT CHARSET=utf8mb4
      COLLATE=utf8mb4_unicode_ci;
    """

    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()