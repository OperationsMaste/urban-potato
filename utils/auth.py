# utils/auth.py
import streamlit as st
import hashlib
import sqlite3
from utils.db import get_db, sync_to_gsheets

def hash_password(pw: str):
    """Hash a password for storing."""
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def check_password(pw: str, pw_hash: str):
    """Check if a password matches its hash."""
    return hash_password(pw) == pw_hash

def login_ui():
    """Display login/signup UI in the sidebar."""
    st.sidebar.markdown("### 🔑 Login / Signup")
    menu = st.sidebar.radio("Choose:", ["Login", "Sign up"], key="auth_menu")

    if menu == "Login":
        with st.sidebar.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.form_submit_button("Login"):
                try:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                    user = cur.fetchone()

                    if user and check_password(password, user["password_hash"]):
                        st.session_state["user"] = dict(user)
                        st.sidebar.success(f"🎉 Logged in as {user['username']} ({user['role']})")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Invalid username or password")

                except sqlite3.Error as e:
                    st.sidebar.error(f"Database error: {str(e)}")
                finally:
                    conn.close()

    elif menu == "Sign up":
        with st.sidebar.form("signup_form"):
            st.markdown("#### 📝 Create Account")
            username = st.text_input("Username", key="signup_username")
            full_name = st.text_input("Full Name", key="signup_full_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            role = st.selectbox("Role", ["participant", "organizer"], key="signup_role")

            if st.form_submit_button("Create Account"):
                # Validate inputs
                if not all([username, full_name, email, password, confirm_password]):
                    st.sidebar.error("❌ Please fill all fields")
                elif password != confirm_password:
                    st.sidebar.error("❌ Passwords don't match")
                elif "@" not in email or "." not in email:
                    st.sidebar.error("❌ Please enter a valid email address")
                else:
                    try:
                        conn = get_db()
                        cur = conn.cursor()

                        # Check if username already exists
                        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                        if cur.fetchone():
                            st.sidebar.error("❌ Username already taken")
                        else:
                            # Create new user
                            cur.execute("""
                                INSERT INTO users (username, password_hash, role, full_name, email)
                                VALUES (?, ?, ?, ?, ?)
                            """, (username, hash_password(password), role, full_name, email))
                            conn.commit()

                            # Sync to Google Sheets if enabled
                            sync_to_gsheets()

                            st.sidebar.success("✅ Account created successfully! Please login.")
                            st.sidebar.info("You can now login with your new credentials")

                    except sqlite3.IntegrityError:
                        st.sidebar.error("❌ Username already taken")
                    except sqlite3.Error as e:
                        st.sidebar.error(f"Database error: {str(e)}")
                    finally:
                        conn.close()

def require_login():
    """Check if user is logged in, otherwise show error and stop execution."""
    if "user" not in st.session_state:
        st.warning("⚠️ Please login to access this feature")
        st.stop()

def logout():
    """Logout the current user."""
    if "user" in st.session_state:
        del st.session_state["user"]
        st.rerun()
