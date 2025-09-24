import streamlit as st
import sqlite3
import hashlib

# Utility to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def login_ui():
    st.subheader("🔑 Login to Fest ERP")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = sqlite3.connect("fest_erp.db")
        cur = conn.cursor()
        cur.execute("SELECT username, password_hash, role, full_name FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password(password, row[1]):
            st.session_state["user"] = {
                "username": row[0],
                "role": row[2],
                "full_name": row[3]
            }
            st.sidebar.success(f"✅ Signed in as {row[3]} ({row[2]})")
            st.rerun()   # ✅ FIXED
        else:
            st.error("❌ Invalid username or password")

def register_ui():
    st.subheader("🆕 Register New User")

    full_name = st.text_input("Full Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["student", "organizer", "admin"])

    if st.button("Register"):
        conn = sqlite3.connect("fest_erp.db")
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (full_name, username, password_hash, role) VALUES (?, ?, ?, ?)",
                (full_name, username, hash_password(password), role),
            )
            conn.commit()
            st.success("🎉 Registration successful! You can now log in.")
        except sqlite3.IntegrityError:
            st.error("⚠️ Username already exists.")
        finally:
            conn.close()
def require_login(required_role=None):
    if "user" not in st.session_state:
        st.warning("Please log in or sign up to access this page.")
        st.stop()
    if required_role and st.session_state["user"]["role"] != required_role:
        st.warning(f"This page is for {required_role}s only.")
        st.stop()
