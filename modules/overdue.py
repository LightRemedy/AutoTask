#modules/overdue.py
import streamlit as st
from core.database import get_connection
from typing import List, Tuple
from datetime import datetime


def show_overdue_tasks():
    """Displays a list of all overdue tasks for the current user."""
    st.title("⚠️ Overdue Tasks")
    conn = get_connection()
    c = conn.cursor()

    # Get current date from session state (for mock date support) or use actual date
    current_date = st.session_state.get('mock_now', datetime.now().date())
    
    c.execute("""
        SELECT task_id, task_name, due_date
        FROM tasks
        WHERE due_date < ? 
        AND completed = 0
        AND created_by = ?
    """, (current_date.strftime("%Y-%m-%d"), st.session_state.username))

    overdue = c.fetchall()

    if not overdue:
        st.success("🎉 No overdue tasks!")
        return

    for task_id, name, due in overdue:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"Due: {due}")
            with col2:
                if st.button("✅ Mark Complete", key=f"overdue_{task_id}"):
                    c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
                    conn.commit()
                    st.rerun()

    conn.close()


def get_overdue_tasks(conn, username: str) -> List[Tuple]:
    """Fetches all overdue tasks from the database for a specific user."""
    c = conn.cursor()
    current_date = st.session_state.get('mock_now', datetime.now().date())
    
    c.execute("""
        SELECT task_id, task_name, due_date
        FROM tasks
        WHERE due_date < ?
        AND completed = 0
        AND created_by = ?
    """, (current_date.strftime("%Y-%m-%d"), username))
    return c.fetchall()


def display_overdue_tasks(tasks: List[Tuple]) -> None:
    """Shows the list of overdue tasks with their details and actions."""
    if not tasks:
        st.success("🎉 No overdue tasks!")
        return

    for task_id, name, due in tasks:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"Due: {due}")
            with col2:
                if st.button("✅ Mark Complete", key=f"overdue_{task_id}"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()

    if 'conn' in locals():
        conn.close()
    