# utils/auth.py
import streamlit as st
import hashlib
from utils.db import get_db

def hash_password(pw: str):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def login_ui():
    st.sidebar.markdown("### 🔑 Login / Signup")
    menu = st.sidebar.radio("Choose:", ["Login", "Sign up"], key="auth_menu")

    if menu == "Login":
        with st.sidebar.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cur.fetchone()
                if user and hash_password(password) == user["password_hash"]:
                    st.session_state["user"] = dict(user)
                    st.sidebar.success(f"Logged in as {user['username']}")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials")
    # ... (rest of your auth logic)
