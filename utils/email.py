# utils/email.py
import streamlit as st
import smtplib
from email.mime.text import MIMEText

def send_email(to, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = st.secrets["SMTP_FROM"]
        msg["To"] = to

        with smtplib.SMTP(st.secrets["SMTP_HOST"], int(st.secrets["SMTP_PORT"])) as server:
            server.starttls()
            server.login(st.secrets["SMTP_USER"], st.secrets["SMTP_PASSWORD"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False
