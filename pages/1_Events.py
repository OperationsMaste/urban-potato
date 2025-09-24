# pages/1_Events.py
import streamlit as st
import pandas as pd
from db import get_db
from auth import require_login
from datetime import datetime
from fest_erp.utils import generate_qr_bytes, create_ticket_image
def format_dt(s):
    try:
        return pd.to_datetime(s)
    except:
        return s

def main():
    st.title("📅 Events — Browse & Register")
    conn = get_db(); cur = conn.cursor()

    # Filters
    q1, q2 = st.columns([3,1])
    with q1:
        search = st.text_input("Search events (title/desc/venue)")
    with q2:
        free_only = st.checkbox("Free events only", value=False)

    cur.execute("SELECT * FROM events ORDER BY start_dt")
    rows = cur.fetchall()
    if not rows:
        st.info("No events yet. Ask organizers to create events.")
        return
    df = pd.DataFrame([dict(r) for r in rows])
    df["start_dt"] = df["start_dt"].apply(format_dt)
    df["end_dt"] = df["end_dt"].apply(format_dt)

    # Filter
    display = df.copy()
    if search:
        display = display[display.apply(lambda r: search.lower() in str(r["title"]).lower() or search.lower() in str(r["description"]).lower() or search.lower() in str(r.get("venue","")).lower(), axis=1)]
    if free_only:
        display = display[display["fee"] == 0]

    for _, ev in display.iterrows():
        st.markdown(f"<div class='card'><div class='event-title'>🎭 {ev['title']}</div>", unsafe_allow_html=True)
        cols = st.columns([3,1])
        with cols[0]:
            st.write(ev["description"])
            st.write(f"**Venue:** {ev.get('venue','TBA')}")
            st.write(f"🕒 {ev['start_dt']} — {ev['end_dt']}")
            st.write(f"Organizer: {ev['organizer_username']}")
            # registrations count
            cur.execute("SELECT COUNT(*) as c FROM registrations WHERE event_id = ?", (ev["id"],))
            cnt = cur.fetchone()["c"]
            st.write(f"Registered: {cnt}/{ev['capacity']}")
        with cols[1]:
            fee_txt = "Free" if ev["fee"] == 0 else f"₹{ev['fee']}"
            st.markdown(f"**{fee_txt}**")
            # Register
            key = f"reg_btn_{ev['id']}"
            if st.button("Register", key=key):
                # open registration form
                with st.form(f"reg_form_{ev['id']}"):
                    name = st.text_input("Full name", value=(st.session_state['user']['full_name'] if 'user' in st.session_state else ""))
                    email = st.text_input("Email")
                    phone = st.text_input("Phone")
                    submitted = st.form_submit_button("Confirm registration")
                    if submitted:
                        username = st.session_state['user']['username'] if 'user' in st.session_state else f"guest_{int(datetime.now().timestamp())}"
                        ts = datetime.now().isoformat()
                        cur.execute("""INSERT INTO registrations (event_id,username,name,email,phone,paid,amount,timestamp)
                                    VALUES (?,?,?,?,?,?,?,?)""",
                                    (ev['id'], username, name, email, phone, 0, ev['fee'], ts))
                        conn.commit()
                        st.success("Registered! If paid events require payment, mark as paid or contact organizer.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    # My registrations (if logged in)
    st.subheader("My Registrations & Tickets")
    if "user" in st.session_state:
        username = st.session_state['user']['username']
        cur.execute("SELECT r.*, e.title, e.start_dt, e.end_dt FROM registrations r JOIN events e ON r.event_id=e.id WHERE r.username = ?", (username,))
        regs = cur.fetchall()
        if not regs:
            st.info("No registrations yet.")
        else:
            dfreg = pd.DataFrame([dict(r) for r in regs])
            st.dataframe(dfreg[["id","title","name","email","phone","paid","amount","timestamp"]])
            for r in regs:
                row = dict(r)
                st.markdown(f"**{row['title']}** — Registered as **{row['name']}**")
                if row["paid"] == 0 and row["amount"] > 0:
                    if st.button(f"Mark mock-paid #{row['id']}"):
                        cur.execute("UPDATE registrations SET paid=1 WHERE id=?", (row["id"],))
                        conn.commit()
                        st.success("Marked as paid (mock). Refresh page.")
                # Ticket / QR
                ticket_text = f"Event:{row['title']}|RegID:{row['id']}|User:{username}"
                qr_bytes = generate_qr_bytes(ticket_text)
                ticket_img = create_ticket_image(row["title"], row["name"], qr_bytes)
                st.image(qr_bytes, width=150, caption="Ticket QR")
                st.download_button("Download Ticket (PNG)", data=ticket_img, file_name=f"ticket_{row['id']}.png", mime="image/png")
    else:
        st.info("Login to view your registrations & tickets.")
