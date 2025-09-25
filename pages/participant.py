# pages/4_Participant.py
import streamlit as st
from utils.db import get_db
from utils.auth import require_login

require_login()
st.title("🎟️ My Registrations")
conn = get_db()
cur = conn.cursor()

# Show user's registrations
cur.execute("""
    SELECT r.*, e.title FROM registrations r
    JOIN events e ON r.event_id = e.id
    WHERE r.username = ?
""", (st.session_state.user["username"],))
registrations = cur.fetchall()

if not registrations:
    st.info("No registrations found")
else:
    for reg in registrations:
        st.subheader(reg["title"])
        st.write(f"**Name:** {reg['name']}")
        st.write(f"**Email:** {reg['email']}")
        st.write(f"**Phone:** {reg['phone']}")
        st.write(f"**Status:** {'Paid' if reg['paid'] else 'Unpaid'}")

        if not reg["paid"] and reg["amount"] > 0:
            if st.button(f"Mock Pay for {reg['title']}"):
                cur.execute("UPDATE registrations SET paid = 1 WHERE id = ?", (reg["id"],))
                conn.commit()
                st.success("Payment marked as complete!")
                st.balloons()
