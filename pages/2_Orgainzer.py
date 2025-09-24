import streamlit as st, pandas as pd
from db import get_db
from auth import require_login
from datetime import datetime

def main():
    require_login("organizer")
    st.title("📌 Organizer Dashboard")
    conn = get_db(); cur = conn.cursor()
    u = st.session_state["user"]["username"]

    with st.form("create_event"):
        t = st.text_input("Event Title")
        d = st.text_area("Description")
        s = st.text_input("Start (YYYY-MM-DD HH:MM)")
        e = st.text_input("End (YYYY-MM-DD HH:MM)")
        cap = st.number_input("Capacity", value=50)
        fee = st.number_input("Fee", value=0)
        sub = st.form_submit_button("Create Event")
        if sub:
            cur.execute("INSERT INTO events (title,description,start_dt,end_dt,capacity,organizer_username,fee) VALUES (?,?,?,?,?,?,?)",
                        (t,d,s,e,cap,u,fee))
            conn.commit()
            st.success("Event created")

    cur.execute("SELECT * FROM events WHERE organizer_username=?", (u,))
    df = pd.DataFrame([dict(r) for r in cur.fetchall()])
    st.subheader("My Events")
    st.dataframe(df)

if __name__ == "__main__":
    main()
