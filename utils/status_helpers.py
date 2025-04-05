#utils/status_helpers.py
import datetime
import streamlit as st
from core.database import get_connection

def get_task_status(conn, task_id):
    """
    Determine the current status of a task. 'completed', 'offtrack', or 'ontrack'.
    """
    c = conn.cursor()

    today = st.session_state.get("mock_now", datetime.date.today())

    c.execute("SELECT completed, due_date FROM tasks WHERE task_id = ?", (task_id,))
    row = c.fetchone()
    if not row:
        return "ontrack"

    completed, due_date = row
    if completed:
        return "completed"

    due_date = datetime.date.fromisoformat(due_date)
    if due_date < today:
        return "offtrack"

    c.execute("""
        SELECT COUNT(*) FROM task_link
        WHERE task_id = ?
        AND pre_task_id IN (
            SELECT task_id FROM tasks WHERE completed = 0
        )
    """, (task_id,))
    incomplete_prereqs = c.fetchone()[0]

    return "offtrack" if incomplete_prereqs > 0 else "ontrack"

def get_group_status(conn, group_id):
    """
    Determine the overall status of a group.
    Returns: 'offtrack', 'ontrack', 'completed', or 'inactive'.
    """
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE group_id = ? AND completed = 0 AND due_date < date('now')
    """, (group_id,))
    if c.fetchone()[0] > 0:
        return "offtrack"

    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id = ? AND completed = 0", (group_id,))
    if c.fetchone()[0] > 0:
        return "ontrack"

    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id = ?", (group_id,))
    return "completed" if c.fetchone()[0] > 0 else "inactive"

def get_status_badge(status):
    """
    Generate a coloured HTML badge representing the status.
    """
    colour_map = {
        "offtrack": "#e74c3c",
        "ontrack": "#f1c40f",
        "completed": "#2ecc71",
        "inactive": "#95a5a6"
    }
    style = (
        f"border-radius:9px; padding:0 7px; font-size:13px; "
        f"color:white; background-color:{colour_map[status]}"
    )
    return f'<span style="{style}">{status.title()}</span>'

def get_task_completion_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total = c.fetchone()[0]
    return completed, total
