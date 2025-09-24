import streamlit as st, pandas as pd
from db import get_db
from auth import require_login, hash_password

def main():
    require_login("admin")
    st.title("🛠️ Admin Dashboard")
    conn = get_db(); cur = conn.cursor()

    with st.form("new_user"):
        u = st.text_input("Username")
        f = st.text_input("Full Name")
        p = st.text_input("Password", type="password")
        r = st.selectbox("Role", ["organizer","participant"])
        sub = st.form_submit_button("Create User")
        if sub:
            cur.execute("INSERT INTO users (username,password_hash,role,full_name) VALUES (?,?,?,?)",
                        (u,hash_password(p),r,f))
            conn.commit()
            st.success("User created")

    st.subheader("All Users")
    cur.execute("SELECT username,role,full_name FROM users")
    st.dataframe(pd.DataFrame(cur.fetchall()))

    st.subheader("All Events")
    cur.execute("SELECT * FROM events")
    st.dataframe(pd.DataFrame(cur.fetchall()))

    st.subheader("All Registrations")
    cur.execute("SELECT * FROM registrations")
    st.dataframe(pd.DataFrame(cur.fetchall()))

if __name__ == "__main__":
    main()
