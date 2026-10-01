import os
import sqlite3
import pymssql
from app.config import settings
from app.path_utils import get_resource_path

def get_db_connection():
    """
    Mengembalikan koneksi database SQL Server (10.81.21.144 / database ipsak413) 
    menggunakan driver 'pymssql' (Tanpa ODBC Driver), 
    dengan fallback ke SQLite jika SQL Server offline.
    """
    db_type = settings.DB_TYPE.lower()
    
    if db_type == "sqlserver":
        try:
            conn = pymssql.connect(
                server=settings.DB_HOST,
                user=settings.DB_USER,
                password=settings.DB_PASS,
                database=settings.DB_NAME,
                port=int(settings.DB_PORT),
                login_timeout=10,
                timeout=30
            )
            return conn
        except Exception:
            # Fallback ke SQLite jika SQL Server offline saat testing
            db_path = get_resource_path(settings.DB_FILE)
            conn = sqlite3.connect(db_path)
            return conn
    else:
        db_path = get_resource_path(settings.DB_FILE)
        conn = sqlite3.connect(db_path)
        return conn
