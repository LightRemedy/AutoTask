import streamlit as st
from db import get_connection

def show_profile():
    st.title("👤 User Profile")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view your profile.")
        return

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT full_name, email, address, gender, contact FROM users WHERE username=?", (username,))
    user_data = c.fetchone()

    if not user_data:
        st.error("Could not retrieve user data.")
        return

    full_name, email, address, gender, contact = user_data

    with st.form("edit_profile_form"):
        st.subheader("Edit Profile")
        new_full_name = st.text_input("Full Name", value=full_name)
        new_email = st.text_input("Email", value=email)
        new_address = st.text_input("Address", value=address)
        new_gender = st.selectbox("Gender", ("Male", "Female", "Other"), index=("Male", "Female", "Other").index(gender))
        new_contact = st.text_input("Contact", value=contact)

        if st.form_submit_button("Update Profile"):
            try:
                c.execute(
                    "UPDATE users SET full_name=?, email=?, address=?, gender=?, contact=? WHERE username=?",
                    (new_full_name, new_email, new_address, new_gender, new_contact, username)
                )
                conn.commit()
                st.success("Profile updated successfully!")
            except Exception as e:
                st.error(f"Error updating profile: {e}")
