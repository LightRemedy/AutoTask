#modules/profile.py
import streamlit as st
from core.database import get_connection


def show_profile():
    """Displays and allows editing of the user's profile information."""
    st.title("�� User Profile")
    username = st.session_state.get("username")

    if not username:
        st.warning("Please log in to view your profile.")
        return

    conn = get_connection()
    c = conn.cursor()
    
    # Get user profile data
    c.execute("""
        SELECT full_name, email, address, gender, contact, view_preference
        FROM users WHERE username = ?
    """, (username,))

    row = c.fetchone()
    if not row:
        st.error("User profile not found.")
        return

    full_name, email, address, gender, contact, view_pref = row

    # Display current profile information
    st.subheader("📝 Current Profile Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Full Name:**")
        st.info(full_name if full_name else "Not set")
        
        st.markdown("**Email:**")
        st.info(email if email else "Not set")
        
        st.markdown("**Address:**")
        st.info(address if address else "Not set")
    
    with col2:
        st.markdown("**Gender:**")
        st.info(gender if gender else "Not set")
        
        st.markdown("**Contact:**")
        st.info(contact if contact else "Not set")

    # Edit profile form
    st.subheader("✏️ Edit Profile")
    with st.form("profile_form"):
        updated_name = st.text_input("Full Name", value=full_name if full_name else "")
        updated_email = st.text_input("Email", value=email if email else "")
        updated_address = st.text_input("Address", value=address if address else "")
        updated_gender = st.selectbox(
            "Gender", 
            ["Male", "Female", "Other", "Prefer not to say"],
            index=["Male", "Female", "Other", "Prefer not to say"].index(gender) if gender else 0
        )
        updated_contact = st.text_input("Contact", value=contact if contact else "")

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
                """, (
                    updated_name,
                    updated_email,
                    updated_address,
                    updated_gender,
                    updated_contact,
                    username
                ))
                conn.commit()
                st.success("Your profile has been updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update profile: {str(e)}")
    
    conn.close()
