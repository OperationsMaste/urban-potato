# pages/2_Organizer.py
import streamlit as st
import pandas as pd
from db import get_db
from auth import require_login
from datetime import datetime

def main():
    require_login("organizer")
    st.title("🧑‍🏫 Organizer Panel")
    conn = get_db(); cur = conn.cursor()
    username = st.session_state['user']['username']

    st.subheader("Create Event")
    with st.form("create_event"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        venue = st.text_input("Venue")
        start_dt = st.text_input("Start (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d 10:00"))
        end_dt = st.text_input("End (YYYY-MM-DD HH:MM)", value=datetime.now().strftime("%Y-%m-%d 12:00"))
        capacity = st.number_input("Capacity", min_value=1, value=50)
        fee = st.number_input("Fee (INR)", min_value=0.0, value=0.0)
        create = st.form_submit_button("Create Event")
        if create:
            cur.execute("""INSERT INTO events (title,description,venue,start_dt,end_dt,capacity,organizer_username,fee,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                        (title, desc, venue, start_dt, end_dt, int(capacity), username, float(fee), datetime.now().isoformat()))
            conn.commit()
            st.success("Event created!")

    st.markdown("---")
    st.subheader("My Events")
    cur.execute("SELECT * FROM events WHERE organizer_username=? ORDER BY start_dt", (username,))
    rows = cur.fetchall()
    if not rows:
        st.info("You have not created any events yet.")
        return
    df = pd.DataFrame([dict(r) for r in rows])
    st.dataframe(df[["id","title","start_dt","end_dt","venue","capacity","fee"]])

    st.subheader("Registrations for my events")
    cur.execute("""SELECT r.*, e.title FROM registrations r
                JOIN events e ON r.event_id=e.id
                WHERE e.organizer_username = ? ORDER BY r.timestamp DESC""", (username,))
    regs = cur.fetchall()
    if not regs:
        st.info("No registrations yet.")
    else:
        dfreg = pd.DataFrame([dict(r) for r in regs])
        st.dataframe(dfreg[["id","title","name","email","phone","paid","amount","timestamp"]])
        csv = dfreg.to_csv(index=False).encode("utf-8")
        st.download_button("Download registrations CSV", csv, "my_event_registrations.csv", mime="text/csv")
