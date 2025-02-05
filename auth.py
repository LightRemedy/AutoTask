# auth.py
import streamlit as st
from db import get_connection

def login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    if user:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        return True
    return False

def register(username, password, full_name, address, gender, contact):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password, full_name, address, gender, contact) VALUES (?,?,?,?,?,?)", 
            (username, password, full_name, address, gender, contact)
        )
        conn.commit()
        st.success("Registration successful. Please login.")
    except Exception as e:
        st.error("Registration failed. Username may already exist.")
