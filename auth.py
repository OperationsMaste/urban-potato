# auth.py
import streamlit as st
from db import get_db, hash_password, check_password
from datetime import datetime

def login_ui():
    st.sidebar.title("🔐 Login / Signup")
    mode = st.sidebar.radio("I want to:", ["Login", "Sign up", "Continue as Guest"])
    conn = get_db(); cur = conn.cursor()

    if mode == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if row and check_password(password, row["password_hash"]):
                st.session_state["user"] = {"username": row["username"], "role": row["role"], "full_name": row["full_name"]}
                st.sidebar.success(f"Signed in as {row['full_name']} ({row['role']})")
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid username or password")
    elif mode == "Sign up":
        with st.sidebar.form("signup_form"):
            st.write("Create Participant account")
            username = st.text_input("Choose username")
            full_name = st.text_input("Full name")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Create account")
            if submit:
                if not (username and full_name and password):
                    st.sidebar.error("Fill all fields")
                else:
                    try:
                        cur.execute("INSERT INTO users (username,password_hash,role,full_name,created_at) VALUES (?,?,?,?,?)",
                                    (username, hash_password(password), "participant", full_name, datetime.now().isoformat()))
                        conn.commit()
                        st.sidebar.success("Account created. Please login.")
                    except Exception as e:
                        st.sidebar.error("Username already exists")
    else:
        st.sidebar.info("Guest mode: limited access. Signup for full features.")

def require_login(required_role=None):
    if "user" not in st.session_state:
        st.warning("Please log in or sign up to access this page.")
        st.stop()
    if required_role and st.session_state["user"]["role"] != required_role:
        st.warning(f"This page is for {required_role}s only.")
        st.stop()
