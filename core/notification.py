#core/notification.py
import streamlit as st
from core.database import get_connection


def send_notification(task_id, task_name, due_date):
    """
    Display a notification for the given task.
    Replace this function with integration to services (e.g., Telegram or Email).
    """
    st.info(f"Reminder: Task '{task_name}' is due on {due_date}!")


def check_notifications(current_date):
    """
    Check all tasks due today or earlier which are incomplete and not notified.
    Triggers notifications and updates their notified flag.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT task_id, task_name, due_date
        FROM tasks
        WHERE due_date <= ? AND completed = 0 AND notified = 0
    """, (current_date.strftime('%Y-%m-%d'),))

    due_tasks = c.fetchall()

    for task_id, task_name, due_date in due_tasks:
        send_notification(task_id, task_name, due_date)
        c.execute("UPDATE tasks SET notified = 1 WHERE task_id = ?", (task_id,))

    conn.commit()
    conn.close()
