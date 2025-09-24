import streamlit as st, pandas as pd
from db import get_db
from auth import require_login
from datetime import datetime

def main():
    st.title("📅 Events & Registrations")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY start_dt")
    events = pd.DataFrame([dict(r) for r in cur.fetchall()])
    if events.empty:
        st.info("No events yet")
        return

    for _, ev in events.iterrows():
        st.subheader(f"{ev['title']} — ₹{ev['fee']}")
        st.write(ev['description'])
        st.write("When:", ev['start_dt'], "to", ev['end_dt'])
        if st.button(f"Register for {ev['title']}", key=ev['id']):
            require_login("participant")
            with st.form(f"reg_{ev['id']}"):
                name = st.text_input("Name", value=st.session_state['user']['full_name'])
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                sub = st.form_submit_button("Confirm Registration")
                if sub:
                    ts = datetime.now().isoformat()
                    cur.execute("""INSERT INTO registrations 
                        (event_id,username,name,email,phone,paid,amount,timestamp) 
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (ev['id'], st.session_state['user']['username'],
                         name,email,phone,0,ev['fee'],ts))
                    conn.commit()
                    st.success("✅ Registered!")

if __name__ == "__main__":
    main()
