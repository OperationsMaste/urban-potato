import streamlit as st
from db import get_db, hash_password, check_password

def login_ui():
    st.sidebar.title("🔑 Login / Signup")
    menu = st.sidebar.radio("Choose", ["Login", "Sign up"])
    conn = get_db(); cur = conn.cursor()

    if menu == "Login":
        u = st.sidebar.text_input("Username")
        p = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            cur.execute("SELECT * FROM users WHERE username=?", (u,))
            user = cur.fetchone()
            if user and check_password(p, user["password_hash"]):
                st.session_state["user"] = dict(user)
                st.sidebar.success(f"Welcome {user['full_name']} ({user['role']})")
            else:
                st.sidebar.error("Invalid credentials")

    elif menu == "Sign up":
        with st.sidebar.form("signup"):
            uname = st.text_input("Username")
            fullname = st.text_input("Full Name")
            pwd = st.text_input("Password", type="password")
            submit = st.form_submit_button("Register")
            if submit:
                try:
                    cur.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                                (uname, hash_password(pwd), "participant", fullname))
                    conn.commit()
                    st.sidebar.success("Account created. Please login.")
                except:
                    st.sidebar.error("Username exists")

def require_login(role=None):
    if "user" not in st.session_state:
        st.warning("Please login first")
        st.stop()
    if role and st.session_state["user"]["role"] != role:
        st.warning(f"{role.capitalize()} only page")
        st.stop()
