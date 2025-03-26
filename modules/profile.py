#modules/profile.py
import streamlit as st
from core.database import get_connection


def show_profile():
    st.title("👤 User Profile")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view your profile.")
        return

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT full_name, email, address, gender, contact
        FROM users WHERE username = ?
    """, (username,))

    row = c.fetchone()
    if not row:
        st.error("User profile not found.")
        return

    full_name, email, address, gender, contact = row

    with st.form("profile_form"):
        st.subheader("Edit Your Details")
        updated_name = st.text_input("Full Name", value=full_name)
        updated_email = st.text_input("Email", value=email)
        updated_address = st.text_input("Address", value=address)
        updated_gender = st.selectbox("Gender", ("Male", "Female", "Other"), index=("Male", "Female", "Other").index(gender))
        updated_contact = st.text_input("Contact", value=contact)

        if st.form_submit_button("Update Profile"):
            try:
                c.execute("""
                    UPDATE users SET
                        full_name = ?,
                        email = ?,
                        address = ?,
                        gender = ?,
                        contact = ?
                    WHERE username = ?
                """, (updated_name, updated_email, updated_address, updated_gender, updated_contact, username))
                conn.commit()
                st.success("Your profile has been updated.")
            except Exception as e:
                st.error(f"Update failed: {e}")
    conn.close()
