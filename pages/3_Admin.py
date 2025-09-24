# pages/3_Admin.py
import streamlit as st
import pandas as pd
from db import get_db, hash_password
from auth import require_login
from datetime import datetime

def main():
    require_login("admin")
    st.title("🛠️ Admin Dashboard")
    conn = get_db(); cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as c FROM users"); users = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM events"); events = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM registrations"); regs = cur.fetchone()["c"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Users", users)
    c2.metric("Events", events)
    c3.metric("Registrations", regs)

    st.markdown("---")
    st.subheader("Create user (organizer or participant)")
    with st.form("create_user"):
        u = st.text_input("Username")
        full = st.text_input("Full name")
        role = st.selectbox("Role", ["organizer","participant"])
        p = st.text_input("Password", type="password")
        submit = st.form_submit_button("Create user")
        if submit:
            try:
                cur.execute("INSERT INTO users (username,password_hash,role,full_name,created_at) VALUES (?,?,?,?,?)",
                            (u, hash_password(p), role, full, datetime.now().isoformat()))
                conn.commit()
                st.success("User created")
            except Exception:
                st.error("Username already exists")

    tab1, tab2, tab3 = st.tabs(["Users","Events","Registrations"])
    with tab1:
        cur.execute("SELECT username,role,full_name,created_at FROM users")
        rows = cur.fetchall()
        st.dataframe(pd.DataFrame([dict(r) for r in rows]))
    with tab2:
        cur.execute("SELECT * FROM events")
        rows = cur.fetchall()
        st.dataframe(pd.DataFrame([dict(r) for r in rows]))
        st.markdown("**Bulk import events (CSV)**")
        up = st.file_uploader("Upload CSV with columns: title,description,venue,start_dt,end_dt,capacity,organizer_username,fee", type=["csv"])
        if up:
            df = pd.read_csv(up)
            for _, r in df.iterrows():
                cur.execute("""INSERT INTO events (title,description,venue,start_dt,end_dt,capacity,organizer_username,fee,created_at)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (r['title'], r.get('description',''), r.get('venue',''), str(r['start_dt']), str(r['end_dt']), int(r.get('capacity',50)), r.get('organizer_username','admin'), float(r.get('fee',0)), datetime.now().isoformat()))
            conn.commit()
            st.success("Imported events from CSV")
    with tab3:
        cur.execute("SELECT r.*, e.title FROM registrations r JOIN events e ON r.event_id=e.id")
        rows = cur.fetchall()
        st.dataframe(pd.DataFrame([dict(r) for r in rows]))
        df = pd.DataFrame([dict(r) for r in rows])
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download all registrations CSV", csv, "registrations.csv", mime="text/csv")
