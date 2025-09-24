# db.py
import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "fest_erp.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw: str):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_password(pw: str, pw_hash: str):
    return hash_password(pw) == pw_hash

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        full_name TEXT,
        created_at TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        venue TEXT,
        start_dt TEXT,
        end_dt TEXT,
        capacity INTEGER,
        organizer_username TEXT,
        fee REAL DEFAULT 0,
        created_at TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        username TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        paid INTEGER DEFAULT 0,
        amount REAL DEFAULT 0,
        timestamp TEXT
    )""")
    # create default admin if missing
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username,password_hash,role,full_name,created_at) VALUES (?,?,?,?,?)",
                    ("admin", hash_password("admin123"), "admin", "Super Admin", datetime.now().isoformat()))
    conn.commit()
    return conn
