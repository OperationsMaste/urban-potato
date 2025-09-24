# fest_erp_google_sheets.py
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date
from dateutil.parser import parse as parsedate
import io
import qrcode
from PIL import Image
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- Constants ---
DB_PATH = "fest_erp.db"
DEFAULT_ADMIN = {"username": "admin", "password": "admin123", "role": "admin", "full_name": "Super Admin", "email": "admin@fest.com"}
USE_GSHEETS = True  # Enable Google Sheets
SMTP_CONFIG = {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "your_email@gmail.com",  # Replace with your email
    "password": "your_app_password",     # Replace with your app password
    "from": "noreply@festerp.com"
}

# --- Initialize Google Sheets ---
if USE_GSHEETS:
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("gsheets_creds.json", scope)
        gc = gspread.authorize(creds)
        sh = gc.open("FestERP").sheet1
        sh.clear()  # Clear sheet on first run
    except Exception as e:
        st.error(f"Google Sheets setup failed: {e}. Using SQLite only.")
        USE_GSHEETS = False

# --- Custom CSS ---
def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { background-color: #f5f5f5; }
        .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; }
        .stTextInput>div>div>input { border-radius: 8px; }
        .stSidebar { background-color: #2c3e50; color: white; }
        .stSidebar .stButton>button { background-color: #3498db; }
        .stSidebar .stTextInput>div>div>input { background-color: #34495e; color: white; }
        .qr-code { text-align: center; margin: 10px 0; }
        .success-box { background-color: #d4edda; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- Utilities ---
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

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
    conn.commit()
    # Create default admin
    cur.execute("SELECT * FROM users WHERE username = ?", (DEFAULT_ADMIN["username"],))
    if not cur.fetchone():
        pw = hash_password(DEFAULT_ADMIN["password"])
        cur.execute("""
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        """, (DEFAULT_ADMIN["username"], pw, DEFAULT_ADMIN["role"], DEFAULT_ADMIN["full_name"], DEFAULT_ADMIN["email"]))
        conn.commit()
        if USE_GSHEETS:
            sync_to_gsheets()

def hash_password(pw: str):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_password(pw: str, pw_hash: str):
    return hash_password(pw) == pw_hash

def row_to_df(rows):
    return pd.DataFrame([dict(ix) for ix in rows]) if rows else pd.DataFrame()

# --- Google Sheets Sync ---
def sync_to_gsheets():
    if not USE_GSHEETS:
        return
    try:
        conn = get_db()
        # Sync users
        users = row_to_df(conn.execute("SELECT * FROM users").fetchall())
        sh.update([users.columns.values.tolist()] + users.values.tolist(), "Users!A1")
        # Sync events
        events = row_to_df(conn.execute("SELECT * FROM events").fetchall())
        sh.update([events.columns.values.tolist()] + events.values.tolist(), "Events!A1")
        # Sync registrations
        regs = row_to_df(conn.execute("SELECT * FROM registrations").fetchall())
        sh.update([regs.columns.values.tolist()] + regs.values.tolist(), "Registrations!A1")
    except Exception as e:
        st.error(f"Google Sheets sync failed: {e}")

# --- Email Notifications ---
def send_email(to, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_CONFIG["from"]
        msg["To"] = to
        with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            server.starttls()
            server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- Auth Helpers ---
def login_ui():
    st.sidebar.markdown("### 🔑 Login / Signup")
    menu = st.sidebar.radio("Choose:", ["Login", "Sign up"], key="auth_menu")

    if menu == "Login":
        with st.sidebar.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.form_submit_button("Login"):
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cur.fetchone()
                if user and check_password(password, user["password_hash"]):
                    st.session_state["user"] = {
                        "username": user["username"],
                        "role": user["role"],
                        "full_name": user["full_name"],
                        "email": user["email"]
                    }
                    st.sidebar.success(f"🎉 Logged in as {user['username']} ({user['role']})")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid credentials")

    elif menu == "Sign up":
        with st.sidebar.form("signup_form"):
            st.markdown("#### 📝 Create Account")
            username = st.text_input("Username", key="signup_username")
            full_name = st.text_input("Full Name", key="signup_full_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            role = st.selectbox("Role", ["participant", "organizer"], key="signup_role")
            if st.form_submit_button("Create Account"):
                if not all([username, full_name, email, password]):
                    st.sidebar.error("❌ Fill all fields")
                else:
                    conn = get_db()
                    cur = conn.cursor()
                    try:
                        cur.execute("""
                            INSERT INTO users (username, password_hash, role, full_name, email)
                            VALUES (?, ?, ?, ?, ?)
                        """, (username, hash_password(password), role, full_name, email))
                        conn.commit()
                        st.sidebar.success("✅ Account created. Please login.")
                        sync_to_gsheets()
                    except sqlite3.IntegrityError:
                        st.sidebar.error("❌ Username already taken")

def require_login():
    if "user" not in st.session_state:
        st.warning("⚠️ Please log in to access this feature.")
        st.stop()

# --- Core UI ---
def admin_panel():
    st.header("📊 Admin Dashboard")
    conn = get_db()
    cur = conn.cursor()

    # User Management
    st.subheader("👥 User Management")
    with st.expander("Create User"):
        with st.form("create_user_form"):
            uname = st.text_input("Username")
            full = st.text_input("Full Name")
            email = st.text_input("Email")
            role = st.selectbox("Role", ["admin", "organizer", "participant"])
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Create User"):
                if not all([uname, full, email, pwd]):
                    st.error("❌ Fill all fields")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO users (username, password_hash, role, full_name, email)
                            VALUES (?, ?, ?, ?, ?)
                        """, (uname, hash_password(pwd), role, full, email))
                        conn.commit()
                        st.success(f"✅ User {uname} created as {role}")
                        sync_to_gsheets()
                    except sqlite3.IntegrityError:
                        st.error("❌ Username exists")

    # Analytics
    st.subheader("📈 Quick Analytics")
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    users_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM events")
    events_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM registrations")
    reg_count = cur.fetchone()["cnt"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Users", users_count)
    col2.metric("Events", events_count)
    col3.metric("Registrations", reg_count)

    # Event Management
    st.subheader("🎭 Event Management")
    with st.expander("Create Event"):
        with st.form("create_event_form"):
            title = st.text_input("Title")
            desc = st.text_area("Description")
            start = st.date_input("Start Date", value=date.today())
            start_time = st.text_input("Start Time (HH:MM)", value="10:00")
            end = st.date_input("End Date", value=date.today())
            end_time = st.text_input("End Time (HH:MM)", value="12:00")
            capacity = st.number_input("Capacity", min_value=1, value=100)
            fee = st.number_input("Fee (₹)", min_value=0.0, value=0.0)
            organizer = st.text_input("Organizer Username", value=st.session_state['user']['username'])
            if st.form_submit_button("Create Event"):
                try:
                    start_dt = datetime.combine(start, datetime.strptime(start_time, "%H:%M").time())
                    end_dt = datetime.combine(end, datetime.strptime(end_time, "%H:%M").time())
                    cur.execute("""
                        INSERT INTO events (title, description, start_dt, end_dt, capacity, organizer_username, fee)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (title, desc, start_dt.isoformat(), end_dt.isoformat(), capacity, organizer, fee))
                    conn.commit()
                    st.success("✅ Event created")
                    sync_to_gsheets()
                except:
                    st.error("❌ Time format error. Use HH:MM")

    # Event List
    cur.execute("SELECT * FROM events ORDER BY start_dt")
    events = row_to_df(cur.fetchall())
    if not events.empty:
        events["start_dt"] = pd.to_datetime(events["start_dt"]).dt.strftime("%Y-%m-%d %H:%M")
        events["end_dt"] = pd.to_datetime(events["end_dt"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(events)
    else:
        st.info("ℹ️ No events yet")

    # Export Data
    st.subheader("📤 Export Data")
    if st.button("Export Events CSV"):
        cur.execute("SELECT * FROM events")
        df = row_to_df(cur.fetchall())
        st.download_button("Download events.csv", df.to_csv(index=False).encode("utf-8"), "events.csv")
    if st.button("Export Registrations CSV"):
        cur.execute("SELECT * FROM registrations")
        df = row_to_df(cur.fetchall())
        st.download_button("Download registrations.csv", df.to_csv(index=False).encode("utf-8"), "registrations.csv")

def organizer_panel():
    st.header("🎤 Organizer Dashboard")
    require_login()
    conn = get_db()
    cur = conn.cursor()
    username = st.session_state["user"]["username"]

    # Create Event
    st.subheader("📅 Create Event")
    with st.form("org_create_event_form"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        start = st.date_input("Start Date", value=date.today())
        start_time = st.text_input("Start Time (HH:MM)", value="10:00")
        end = st.date_input("End Date", value=date.today())
        end_time = st.text_input("End Time (HH:MM)", value="12:00")
        capacity = st.number_input("Capacity", min_value=1, value=50)
        fee = st.number_input("Fee (₹)", min_value=0.0, value=0.0)
        if st.form_submit_button("Create"):
            try:
                start_dt = datetime.combine(start, datetime.strptime(start_time, "%H:%M").time())
                end_dt = datetime.combine(end, datetime.strptime(end_time, "%H:%M").time())
                cur.execute("""
                    INSERT INTO events (title, description, start_dt, end_dt, capacity, organizer_username, fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, desc, start_dt.isoformat(), end_dt.isoformat(), capacity, username, fee))
                conn.commit()
                st.success("✅ Event created")
                sync_to_gsheets()
            except:
                st.error("❌ Time format error. Use HH:MM")

    # My Events
    st.subheader("📋 Your Events")
    cur.execute("SELECT * FROM events WHERE organizer_username = ? ORDER BY start_dt", (username,))
    events = row_to_df(cur.fetchall())
    if events.empty:
        st.info("ℹ️ You have no events yet.")
    else:
        for _, ev in events.iterrows():
            st.markdown(f"### {ev['title']}")
            st.write(ev['description'])
            st.write(f"**When:** {pd.to_datetime(ev['start_dt']).strftime('%Y-%m-%d %H:%M')} to {pd.to_datetime(ev['end_dt']).strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Capacity:** {ev['capacity']} | **Fee:** ₹{ev['fee']}")
            if st.button(f"View Registrations (Event {ev['id']})"):
                cur.execute("SELECT * FROM registrations WHERE event_id = ?", (ev['id'],))
                regs = row_to_df(cur.fetchall())
                if regs.empty:
                    st.info("ℹ️ No registrations yet.")
                else:
                    st.dataframe(regs)

def participant_panel():
    st.header("🎟️ Participant Portal")
    conn = get_db()
    cur = conn.cursor()

    # Event List
    st.subheader("📅 Available Events")
    cur.execute("SELECT * FROM events ORDER BY start_dt")
    events = row_to_df(cur.fetchall())
    if events.empty:
        st.info("ℹ️ No events yet")
        return
    events["start_dt"] = pd.to_datetime(events["start_dt"])
    events["end_dt"] = pd.to_datetime(events["end_dt"])

    # Search & Filter
    col1, col2 = st.columns([3, 1])
    with col1:
        qstr = st.text_input("🔍 Search by title/description")
    with col2:
        only_free = st.checkbox("Only free events", value=False)

    display = events.copy()
    if qstr:
        display = display[display.apply(lambda r: qstr.lower() in str(r["title"]).lower() or qstr.lower() in str(r["description"]).lower(), axis=1)]
    if only_free:
        display = display[display["fee"] == 0]

    # Event Cards
    for _, ev in display.iterrows():
        st.markdown(f"### {ev['title']} — ₹{ev['fee']}")
        st.write(ev['description'])
        st.write(f"**When:** {ev['start_dt'].strftime('%Y-%m-%d %H:%M')} to {ev['end_dt'].strftime('%Y-%m-%d %H:%M')}")
        cur.execute("SELECT COUNT(*) as cnt FROM registrations WHERE event_id = ?", (ev['id'],))
        cnt = cur.fetchone()["cnt"]
        st.write(f"**Registered:** {cnt}/{ev['capacity']}")
        if cnt < ev['capacity']:
            if st.button(f"Register (Event {ev['id']})"):
                with st.form(f"regform_{ev['id']}"):
                    name = st.text_input("Full Name", value=st.session_state['user']['full_name'])
                    email = st.text_input("Email", value=st.session_state['user']['email'])
                    phone = st.text_input("Phone")
                    if st.form_submit_button("Submit Registration"):
                        username = st.session_state['user']['username']
                        ts = datetime.now().isoformat()
                        cur.execute("""
                            INSERT INTO registrations (event_id, username, name, email, phone, paid, amount, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (ev['id'], username, name, email, phone, 0, ev['fee'], ts))
                        conn.commit()
                        st.markdown(f"""
                        <div class="success-box">
                            ✅ Registered successfully!
                        </div>
                        """, unsafe_allow_html=True)
                        # Send email
                        subject = f"Registration Confirmation: {ev['title']}"
                        body = f"""
                        Hi {name},
                        You have successfully registered for {ev['title']}!
                        Event Date: {ev['start_dt'].strftime('%Y-%m-%d %H:%M')}
                        Fee: ₹{ev['fee']}
                        """
                        send_email(email, subject, body)
                        # Generate QR
                        qr = qrcode.make(f"Event: {ev['title']}\nName: {name}\nEmail: {email}")
                        img = Image.open(io.BytesIO(qr.png()))
                        st.image(img, caption="Your Ticket QR Code", width=200, use_column_width=False)
                        sync_to_gsheets()
        else:
            st.warning("⚠️ Event full")

    # My Registrations
    st.subheader("📝 My Registrations")
    if "user" in st.session_state:
        username = st.session_state["user"]["username"]
        cur.execute("""
            SELECT r.*, e.title FROM registrations r
            JOIN events e ON r.event_id = e.id
            WHERE r.username = ?
        """, (username,))
        regs = row_to_df(cur.fetchall())
        if regs.empty:
            st.info("ℹ️ No registrations found")
        else:
            st.dataframe(regs)
            for _, r in regs.iterrows():
                if r['paid'] == 0 and r['amount'] > 0:
                    if st.button(f"Mock Pay (Registration {r['id']})"):
                        cur.execute("UPDATE registrations SET paid = 1 WHERE id = ?", (r['id'],))
                        conn.commit()
                        st.markdown(f"""
                        <div class="success-box">
                            ✅ Payment marked as complete!
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                        sync_to_gsheets()

# --- Main App ---
def main():
    st.set_page_config(page_title="Fest ERP", layout="wide", page_icon="🎉")
    inject_custom_css()
    init_db()

    # Always show login/sidebar
    login_ui()

    # Navigation
    menu = ["Home", "Events"]
    if "user" in st.session_state:
        role = st.session_state["user"]["role"]
        if role == "admin":
            menu.extend(["Admin Panel", "My Account", "Logout"])
        elif role == "organizer":
            menu.extend(["Organizer Panel", "My Account", "Logout"])
        elif role == "participant":
            menu.extend(["My Registrations", "My Account", "Logout"])
    else:
        menu.append("Login/Signup")

    choice = st.sidebar.selectbox("📌 Navigation", menu)

    if choice == "Home":
        st.title("🎉 Inter-College Festival ERP")
        st.write("Welcome! Use the sidebar to navigate.")
        st.markdown("""
        **Features:**
        - Role-based access (Admin/Organizer/Participant)
        - Event creation & registration
        - QR code tickets
        - Email notifications
        - Google Sheets sync
        """)
    elif choice == "Events":
        participant_panel()
    elif choice == "Admin Panel":
        if "user" not in st.session_state or st.session_state["user"]["role"] != "admin":
            st.warning("⚠️ Admin-only area")
        else:
            admin_panel()
    elif choice == "Organizer Panel":
        if "user" not in st.session_state or st.session_state["user"]["role"] != "organizer":
            st.warning("⚠️ Organizer-only area")
        else:
            organizer_panel()
    elif choice == "My Registrations":
        participant_panel()
    elif choice == "My Account":
        if "user" in st.session_state:
            st.write("Logged in as:", st.session_state['user'])
            if st.button("Logout"):
                st.session_state.pop("user")
                st.rerun()
        else:
            st.info("ℹ️ Not logged in")
    elif choice == "Logout":
        if "user" in st.session_state:
            st.session_state.pop("user")
            st.rerun()

if __name__ == "__main__":
    main()
