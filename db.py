import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '9888',  # Ton mot de passe MySQL
    'database': 'plash_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.Cursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)
