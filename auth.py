import streamlit as st
from db import get_connection
import re

def login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    
    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

def register(username, password, full_name, address, gender, contact):
    if not username or not password:
        st.error("Username and password are required")
        return False
        
    if not is_valid_password(password):
        st.error("Password must contain:")
        st.error("- At least 8 characters")
        st.error("- A mix of letters and numbers")
        st.error("- At least one special character")
        return False

    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute(
            "INSERT INTO users (username, password, full_name, address, gender, contact) VALUES (?,?,?,?,?,?)",
            (username, password, full_name, address, gender, contact)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists")
        return False
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
