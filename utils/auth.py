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

    elif menu == "Sign up":
        with st.sidebar.form("signup"):
            st.markdown("#### 📝 Create Account")
            username = st.text_input("Username")
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["participant", "organizer"])
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
                    except sqlite3.IntegrityError:
                        st.sidebar.error("❌ Username already taken")
