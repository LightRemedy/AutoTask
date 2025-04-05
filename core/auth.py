#core/auth.py
import sqlite3
from core.database import get_connection

def login(username: str, password: str) -> bool:
    """Checks if the provided username and password match a user in the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username COLLATE NOCASE = ?", (username,))
    result = c.fetchone()
    return result is not None and result[0] == password

def register(username: str, password: str, full_name: str, email: str,
             address: str, gender: str, contact: str) -> bool:
    """Creates a new user account with the provided information."""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, full_name, email, address, gender, contact)"
                  " VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (username, password, full_name, email, address, gender, contact))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
