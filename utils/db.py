# utils/db.py
import sqlite3
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd

DB_PATH = "fest_erp.db"

# Initialize Google Sheets
if "GSHEETS_CREDENTIALS_JSON" in st.secrets:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(st.secrets["GSHEETS_CREDENTIALS_JSON"]),
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open(st.secrets["GSHEETS_SHEET_NAME"]).sheet1
    except Exception as e:
        st.error(f"Google Sheets setup failed: {e}")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        full_name TEXT,
        email TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        start_dt TEXT,
        end_dt TEXT,
        capacity INTEGER,
        organizer_username TEXT,
        fee REAL DEFAULT 0
    )
    """)

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
    )
    """)

    # Create default admin
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", hash_password("admin123"), "admin", "Super Admin", "admin@fest.com"))
    conn.commit()

def sync_to_gsheets():
    if "GSHEETS_CREDENTIALS_JSON" not in st.secrets:
        return
    try:
        conn = get_db()
        # Sync users
        users = pd.DataFrame(conn.execute("SELECT * FROM users").fetchall())
        sh.update([users.columns.values.tolist()] + users.values.tolist(), "Users!A1")
        # Sync events
        events = pd.DataFrame(conn.execute("SELECT * FROM events").fetchall())
        sh.update([events.columns.values.tolist()] + events.values.tolist(), "Events!A1")
        # Sync registrations
        regs = pd.DataFrame(conn.execute("SELECT * FROM registrations").fetchall())
        sh.update([regs.columns.values.tolist()] + regs.values.tolist(), "Registrations!A1")
    except Exception as e:
        st.error(f"Google Sheets sync failed: {e}")

def hash_password(pw: str):
    import hashlib
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()
