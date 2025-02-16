import streamlit as st
from db import get_connection

def show_profile():
    st.title("👤 User Profile")
    if "username" in st.session_state and st.session_state.username:
        st.write(f"Username: {st.session_state.username}")

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT full_name, address, gender, contact FROM users WHERE username=?", (st.session_state.username,))
        user_data = c.fetchone()

        if user_data:
            full_name, address, gender, contact = user_data
            st.write(f"Full Name: {full_name}")
            st.write(f"Address: {address}")
            st.write(f"Gender: {gender}")
            st.write(f"Contact: {contact}")

    else:
        st.warning("Please log in to view your profile.")
