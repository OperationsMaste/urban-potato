
# fest_erp.py
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime, date
from dateutil.parser import parse as parsedate
import io

DB_PATH = "fest_erp.db"

# -------------------------
# Utilities
# -------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # users: id, username, password_hash, role (admin/organizer/participant), full_name, org_id
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        full_name TEXT,
        org TEXT
    )
    """)
    # events: id, title, description, start_dt, end_dt, capacity, organizer_username, fee
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
    # registrations: id, event_id, username, name, email, phone, paid (0/1), amount, timestamp
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
    # create default admin if not exists
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        pw = hash_password("admin123")
        cur.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                    ("admin", pw, "admin", "Super Admin"))
        conn.commit()

def hash_password(pw: str):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_password(pw: str, pw_hash: str):
    return hash_password(pw) == pw_hash

def row_to_df(rows):
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(ix) for ix in rows])

# -------------------------
# Auth helpers
# -------------------------
def login_ui():
    st.sidebar.title("Login / Signup")
    menu = st.sidebar.selectbox("Choose", ["Login", "Sign up", "Continue as Guest"])
    if menu == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cur.fetchone()
            if user and check_password(password, user["password_hash"]):
                st.session_state["user"] = {"username": user["username"], "role": user["role"], "full_name": user["full_name"]}
                st.sidebar.success(f"Logged in as {user['username']} ({user['role']})")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")
    elif menu == "Sign up":
        with st.sidebar.form("signup"):
            st.write("Create Participant Account")
            username = st.text_input("Choose username")
            full_name = st.text_input("Full name")
            password = st.text_input("Password", type="password")
            email = st.text_input("Email (optional)")
            submitted = st.form_submit_button("Create account")
            if submitted:
                if not username or not password or not full_name:
                    st.sidebar.error("Please fill username, password and full name")
                else:
                    conn = get_db(); cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                                    (username, hash_password(password), "participant", full_name))
                        conn.commit()
                        st.sidebar.success("Account created. Please login.")
                    except sqlite3.IntegrityError:
                        st.sidebar.error("Username already taken")
    else:
        st.sidebar.info("Guest mode: limited access")

def require_login():
    if "user" not in st.session_state:
        st.warning("Please log in or sign up to access full features.")
        st.stop()

# -------------------------
# Core UI pieces
# -------------------------
def admin_panel():
    st.header("Admin Dashboard")
    conn = get_db(); cur = conn.cursor()
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Create Organizer / Participant account")
        with st.form("create_user"):
            uname = st.text_input("Username")
            full = st.text_input("Full name")
            role = st.selectbox("Role", ["organizer", "participant"])
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create user")
            if submitted:
                if not (uname and pwd and full):
                    st.error("Fill all fields")
                else:
                    try:
                        cur.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                                    (uname, hash_password(pwd), role, full))
                        conn.commit()
                        st.success(f"User {uname} created as {role}")
                    except sqlite3.IntegrityError:
                        st.error("Username exists")
    with c2:
        st.subheader("Quick analytics")
        cur.execute("SELECT COUNT(*) as cnt FROM users")
        users_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM events")
        events_count = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM registrations")
        reg_count = cur.fetchone()["cnt"]
        st.metric("Users", users_count)
        st.metric("Events", events_count)
        st.metric("Registrations", reg_count)

    st.markdown("---")
    st.subheader("Events Management")
    if st.button("Create Sample Event"):
        cur.execute("""INSERT INTO events (title,description,start_dt,end_dt,capacity,organizer_username,fee)
            VALUES (?,?,?,?,?,?,?)""",
            ("Sample Dance", "Intercollege dance competition", datetime.now().isoformat(), (datetime.now()).isoformat(), 100, st.session_state['user']['username'], 50.0))
        conn.commit()
        st.success("Sample event added")
    # Create event form
    with st.expander("Create new event"):
        with st.form("create_event"):
            title = st.text_input("Title")
            desc = st.text_area("Description")
            start = st.date_input("Start date", value=date.today())
            start_time = st.text_input("Start time (HH:MM)", value="10:00")
            end = st.date_input("End date", value=date.today())
            end_time = st.text_input("End time (HH:MM)", value="12:00")
            capacity = st.number_input("Capacity", min_value=1, value=100)
            fee = st.number_input("Fee (INR)", min_value=0.0, value=0.0)
            organizer = st.text_input("Organizer username", value=st.session_state['user']['username'])
            ce = st.form_submit_button("Create Event")
            if ce:
                try:
                    start_dt = datetime.combine(start, datetime.strptime(start_time, "%H:%M").time())
                    end_dt = datetime.combine(end, datetime.strptime(end_time, "%H:%M").time())
                except Exception as e:
                    st.error("Time format error. Use HH:MM")
                    start_dt = end_dt = None
                if start_dt and end_dt:
                    cur.execute("""INSERT INTO events (title,description,start_dt,end_dt,capacity,organizer_username,fee)
                        VALUES (?,?,?,?,?,?,?)""",
                        (title, desc, start_dt.isoformat(), end_dt.isoformat(), int(capacity), organizer, float(fee)))
                    conn.commit()
                    st.success("Event created")

    # list & edit events
    cur.execute("SELECT * FROM events ORDER BY start_dt")
    events = cur.fetchall()
    df = row_to_df(events)
    if not df.empty:
        df_display = df.copy()
        df_display["start_dt"] = pd.to_datetime(df_display["start_dt"]).dt.strftime("%Y-%m-%d %H:%M")
        df_display["end_dt"] = pd.to_datetime(df_display["end_dt"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(df_display)
    else:
        st.info("No events yet")

    # Export CSVs
    st.subheader("Export data")
    if st.button("Export events CSV"):
        cur.execute("SELECT * FROM events")
        df = row_to_df(cur.fetchall())
        st.download_button("Download events.csv", df.to_csv(index=False).encode("utf-8"), "events.csv")
    if st.button("Export registrations CSV"):
        cur.execute("SELECT * FROM registrations")
        df = row_to_df(cur.fetchall())
        st.download_button("Download registrations.csv", df.to_csv(index=False).encode("utf-8"), "registrations.csv")

def organizer_panel():
    st.header("Organizer Dashboard")
    require_login()
    conn = get_db(); cur = conn.cursor()
    username = st.session_state["user"]["username"]
    st.subheader("Create Event")
    with st.form("org_create_event"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        start = st.date_input("Start date", value=date.today())
        start_time = st.text_input("Start time (HH:MM)", value="10:00")
        end = st.date_input("End date", value=date.today())
        end_time = st.text_input("End time (HH:MM)", value="12:00")
        capacity = st.number_input("Capacity", min_value=1, value=50)
        fee = st.number_input("Fee (INR)", min_value=0.0, value=0.0)
        ce = st.form_submit_button("Create")
        if ce:
            try:
                start_dt = datetime.combine(start, datetime.strptime(start_time, "%H:%M").time())
                end_dt = datetime.combine(end, datetime.strptime(end_time, "%H:%M").time())
            except:
                st.error("Time format error.")
                start_dt = end_dt = None
            if start_dt:
                cur.execute("""INSERT INTO events (title,description,start_dt,end_dt,capacity,organizer_username,fee)
                    VALUES (?,?,?,?,?,?,?)""",
                    (title, desc, start_dt.isoformat(), end_dt.isoformat(), int(capacity), username, float(fee)))
                conn.commit()
                st.success("Event created")

    st.markdown("---")
    st.subheader("Your Events & Registrations")
    cur.execute("SELECT * FROM events WHERE organizer_username = ? ORDER BY start_dt", (username,))
    events = row_to_df(cur.fetchall())
    if events.empty:
        st.info("You have no events yet.")
        return
    for _, ev in events.iterrows():
        st.markdown(f"### {ev['title']}")
        st.write(ev['description'])
        st.write("When:", pd.to_datetime(ev['start_dt']).strftime("%Y-%m-%d %H:%M"), "to", pd.to_datetime(ev['end_dt']).strftime("%Y-%m-%d %H:%M"))
        st.write("Capacity:", ev['capacity'], " | Fee:", ev['fee'])
        if st.button(f"View registrations for {ev['id']}"):
            cur.execute("SELECT * FROM registrations WHERE event_id = ?", (ev['id'],))
            regs = row_to_df(cur.fetchall())
            if regs.empty:
                st.info("No registrations yet.")
            else:
                st.dataframe(regs)

def participant_panel():
    st.header("Participant Portal")
    # show events
    conn = get_db(); cur = conn.cursor()
    st.subheader("Available Events")
    q = "SELECT * FROM events ORDER BY start_dt"
    cur.execute(q)
    events = row_to_df(cur.fetchall())
    if events.empty:
        st.info("No events yet")
        return
    events["start_dt"] = pd.to_datetime(events["start_dt"])
    events["end_dt"] = pd.to_datetime(events["end_dt"])
    # Show simple search/filter
    col1, col2 = st.columns([3,1])
    with col1:
        qstr = st.text_input("Search by title/description")
    with col2:
        only_free = st.checkbox("Only free events", value=False)

    display = events.copy()
    if qstr:
        display = display[display.apply(lambda r: qstr.lower() in str(r["title"]).lower() or qstr.lower() in str(r["description"]).lower(), axis=1)]
    if only_free:
        display = display[display["fee"] == 0]
    # show
    for _, ev in display.iterrows():
        st.markdown(f"### {ev['title']} — ₹{ev['fee']}")
        st.write(ev['description'])
        st.write("When:", ev['start_dt'].strftime("%Y-%m-%d %H:%M"), "to", ev['end_dt'].strftime("%Y-%m-%d %H:%M"))
        # compute current registrations
        cur.execute("SELECT COUNT(*) as cnt FROM registrations WHERE event_id = ?", (ev['id'],))
        cnt = cur.fetchone()["cnt"]
        st.write(f"Registered: {cnt}/{ev['capacity']}")
        # Register button only if capacity remains
        if cnt < ev['capacity']:
            open_reg = st.button(f"Register (Event {ev['id']})")
            if open_reg:
                with st.form(f"regform_{ev['id']}"):
                    name = st.text_input("Full name", value=(st.session_state['user']['full_name'] if 'user' in st.session_state else ""))
                    email = st.text_input("Email")
                    phone = st.text_input("Phone")
                    submitted = st.form_submit_button("Submit registration")
                    if submitted:
                        # If user logged in, set username else guest_{ts}
                        username = st.session_state['user']['username'] if 'user' in st.session_state else f"guest_{int(datetime.now().timestamp())}"
                        ts = datetime.now().isoformat()
                        cur.execute("""INSERT INTO registrations (event_id,username,name,email,phone,paid,amount,timestamp)
                                    VALUES (?,?,?,?,?,?,?,?)""",
                                    (ev['id'], username, name, email, phone, 0, ev['fee'], ts))
                        conn.commit()
                        st.success("Registered. Proceed to payment (if fee > 0).")
        else:
            st.warning("Event full")

    st.markdown("---")
    st.subheader("My Registrations")
    if "user" in st.session_state and st.session_state["user"]["role"] in ["participant","organizer","admin"]:
        username = st.session_state["user"]["username"]
        cur.execute("SELECT r.*, e.title FROM registrations r JOIN events e ON r.event_id = e.id WHERE r.username = ?", (username,))
        regs = row_to_df(cur.fetchall())
        if regs.empty:
            st.info("No registrations found")
        else:
            st.dataframe(regs)
            # allow payment toggling (mock)
            for _, r in regs.iterrows():
                if r['paid'] == 0 and r['amount'] > 0:
                    if st.button(f"Mock Pay {r['id']}"):
                        cur.execute("UPDATE registrations SET paid = 1 WHERE id = ?", (r['id'],))
                        conn.commit()
                        st.success("Payment marked as complete (mock). Refresh page.")
    else:
        st.info("Login to view your registrations")

# -------------------------
# Public home & nav
# -------------------------
def home():
    st.title("Inter-College Festival ERP")
    st.write("Welcome! Use the side bar to login/sign up and navigate.")
    st.markdown("""
    **Features:**  
    - Role-based access (Admin / Organizer / Participant)  
    - Create and manage events, capacities and fees  
    - Participant registration and mock payments  
    - CSV export of events / registrations  
    - Simple dashboards for Admins and Organizers
    """)

def main():
    st.set_page_config(page_title="Fest ERP", layout="wide")
    init_db()
    login_ui()

    menu = ["Home","Events","Dashboard","My Account","Admin Panel"]
    if "user" in st.session_state:
        role = st.session_state["user"]["role"]
        if role == "organizer":
            menu = ["Home","Events","Organizer Panel","My Account","Logout"]
        elif role == "participant":
            menu = ["Home","Events","My Registrations","My Account","Logout"]
        elif role == "admin":
            menu = ["Home","Events","Admin Panel","My Account","Logout"]
    else:
        menu = ["Home","Events","Login/Signup"]

    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Home":
        home()
    elif choice == "Events":
        participant_panel()
    elif choice in ("Dashboard","Admin Panel"):
        if "user" not in st.session_state or st.session_state["user"]["role"] != "admin":
            st.warning("Admin-only area")
            return
        admin_panel()
    elif choice == "Organizer Panel":
        if "user" not in st.session_state or st.session_state["user"]["role"] != "organizer":
            st.warning("Organizer-only area")
            return
        organizer_panel()
    elif choice == "My Registrations":
        participant_panel()
    elif choice == "My Account":
        if "user" not in st.session_state:
            st.info("Not logged in")
        else:
            st.write("Logged in as:", st.session_state['user'])
            if st.button("Logout"):
                st.session_state.pop("user")
                st.rerun()
    elif choice == "Logout":
        if "user" in st.session_state:
            st.session_state.pop("user")
            st.rerun()
    elif choice == "Login/Signup":
        st.write("Use the left sidebar to login or sign up.")
    else:
        st.write("Unknown choice")

if __name__ == "__main__":
    main()
