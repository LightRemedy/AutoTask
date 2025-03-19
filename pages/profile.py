import streamlit as st
from db import get_connection

### User Profile Module
# This module handles user profile management, allowing users to:
# * View their current profile information
# * Update their personal details
# * Manage account settings

def show_profile():
    ### Main Profile Display Function
    # Shows and handles updates to user profile information
    
    st.title("👤 User Profile")
    username = st.session_state.get("username")

    ### Authentication Check
    # Ensures user is logged in before showing profile
    if not username:
        st.warning("Please log in to view your profile.")
        return

    ### Database Connection and Data Retrieval
    # Fetches current user data from database
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT full_name, email, address, gender, contact FROM users WHERE username=?", (username,))
    user_data = c.fetchone()

    ### Data Validation
    # Ensures user data exists in database
    if not user_data:
        st.error("Could not retrieve user data.")
        return

    ### Data Unpacking
    # Extract user information from database result
    full_name, email, address, gender, contact = user_data

    ### Profile Edit Form
    # Creates form with current values pre-filled
    # Allows updating of:
    # * Full Name
    # * Email
    # * Address
    # * Gender
    # * Contact Information
    with st.form("edit_profile_form"):
        st.subheader("Edit Profile")
        new_full_name = st.text_input("Full Name", value=full_name)
        new_email = st.text_input("Email", value=email)
        new_address = st.text_input("Address", value=address)
        new_gender = st.selectbox("Gender", ("Male", "Female", "Other"), 
                                index=("Male", "Female", "Other").index(gender))
        new_contact = st.text_input("Contact", value=contact)

        ### Form Submission Handler
        # Updates user information in database
        # Provides success/error feedback to user
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
