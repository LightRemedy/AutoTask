# tasks.py
import streamlit as st
from db import get_connection
import datetime

def get_tasks_by_template(template_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT task_id, task_name, due_date, completed FROM tasks WHERE template_id=?", (template_id,))
    return c.fetchall()

def mark_task_complete(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
    conn.commit()

def send_notification(task_id, task_name, due_date):
    # Here you could integrate an external notification service (e.g., Telegram)
    st.info(f"Notification: Task '{task_name}' is due on {due_date}!")

def check_notifications(current_date):
    current_ordinal = current_date.toordinal()
    conn = get_connection()
    c = conn.cursor()
    
    # Get tasks where notification should be triggered
    c.execute('''
        SELECT task_id, task_name, due_date 
        FROM tasks 
        WHERE (due_date - notification_days) <= ? 
          AND completed=0 
          AND notified=0
    ''', (current_ordinal,))
    
    due_tasks = c.fetchall()
    for task in due_tasks:
        task_id, task_name, due_ordinal = task
        due_date = datetime.date.fromordinal(due_ordinal)
        send_notification(task_id, task_name, due_date)
        
        # Update notified status
        c.execute("UPDATE tasks SET notified=1 WHERE task_id=?", (task_id,))
    conn.commit()
