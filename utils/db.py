# utils/db.py
import os
import sqlite3
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()
DB_PATH = "fest_erp.db"
USE_GSHEETS = os.getenv("GSHEETS_CREDENTIALS_JSON") is not None

# Initialize Google Sheets
if USE_GSHEETS:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(os.getenv("GSHEETS_CREDENTIALS_JSON")),
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open(os.getenv("GSHEETS_SHEET_NAME")).sheet1
    except Exception as e:
        print(f"Google Sheets setup failed: {e}")
        USE_GSHEETS = False

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Create tables if they don't exist
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
    # ... (rest of your table creation code)
    conn.commit()

def sync_to_gsheets():
    if not USE_GSHEETS:
        return
    try:
        conn = get_db()
        # Sync users, events, registrations to Google Sheets
        # ... (your existing sync logic)
    except Exception as e:
        print(f"Google Sheets sync failed: {e}")
      
