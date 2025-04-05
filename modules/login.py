#modules/login.py
import streamlit as st
from core.database import get_connection
from core.auth import login, register


def show_login_page():
    """Displays the login page with options to log in or create a new account."""
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none; }
            .main > div { max-width: 800px; padding: 2rem; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col2:
        if not st.session_state.get("show_register", False):
            st.title("🔐 AutoTask Login")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if login(username, password):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT view_preference FROM users WHERE username=?", (username,))
                        result = c.fetchone()
                        st.session_state.update({
                            "logged_in": True,
                            "username": username,
                            "view_preference": result[0] if result else "calendar",
                            "current_page": "Dashboard"
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")

            if st.button("Create New Account"):
                st.session_state.show_register = True
                st.rerun()
        else:
            st.title("📝 User Registration")
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                address = st.text_input("Address")
                gender = st.selectbox("Gender", ("Male", "Female", "Other"))
                contact = st.text_input("Contact")

                if st.form_submit_button("Register"):
                    if register(new_username, new_password, full_name, email, address, gender, contact):
                        st.success("Registration successful! Please login.")
                        st.session_state.show_register = False
                        st.rerun()

            if st.button("← Back to Login"):
                st.session_state.show_register = False
                st.rerun()

