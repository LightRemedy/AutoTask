#core/notification.py
import streamlit as st
from core.database import get_connection
import asyncio
from telegram import Bot
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime, date
from core.date_utils import get_current_date, format_date

async def send_telegram_message(message):
    """
    Send a message via Telegram bot
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Telegram configuration is missing. Please set up TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        st.error(f"Failed to send Telegram message: {str(e)}")

def send_notification(task_id, task_name, due_date, is_offtrack=False):
    """
    Send a notification for the given task via Telegram and display in Streamlit.
    
    Args:
        task_id: ID of the task
        task_name: Name of the task
        due_date: Due date of the task
        is_offtrack: Whether this is an off-track notification
    """
    if is_offtrack:
        message = f"⚠️ OVERDUE TASK ALERT:\nTask: {task_name}\nDue Date: {due_date}\nStatus: Off Track - Action Required!"
    else:
        message = f"🔔 Task Reminder:\nTask: {task_name}\nDue Date: {due_date}"
    
    # Display in Streamlit
    if is_offtrack:
        st.warning(message)
    else:
        st.info(message)
    
    # Check if telegram_notify is enabled for this task
    conn = get_connection()
    c = conn.cursor()
    
    # Check if the column exists
    c.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'telegram_notify' in columns:
        c.execute("SELECT telegram_notify FROM tasks WHERE task_id = ?", (task_id,))
        result = c.fetchone()
        should_notify = result[0] if result else True
    else:
        should_notify = True  # Default to True if column doesn't exist
    
    conn.close()
    
    # Send via Telegram if enabled
    if should_notify:
        asyncio.run(send_telegram_message(message))

def ensure_notification_column(conn):
    """Ensure the last_notification_date column exists and update it for existing users."""
    c = conn.cursor()
    
    # Check if column exists
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'last_notification_date' not in columns:
        try:
            c.execute('ALTER TABLE users ADD COLUMN last_notification_date TEXT')
            conn.commit()
        except Exception as e:
            print(f"Column already exists or error: {e}")
            conn.rollback()

def check_notifications(conn, username):
    """Check for overdue tasks and send notifications."""
    try:
        c = conn.cursor()
        current_date = get_current_date()
        today = format_date(current_date)
        
        # Check if required columns exist
        c.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in c.fetchall()]
        
        # Add missing columns if needed
        if 'last_notification_date' not in columns:
            c.execute('ALTER TABLE tasks ADD COLUMN last_notification_date TEXT')
        if 'telegram_notify' not in columns:
            c.execute('ALTER TABLE tasks ADD COLUMN telegram_notify INTEGER DEFAULT 1')
        if 'notified' not in columns:
            c.execute('ALTER TABLE tasks ADD COLUMN notified INTEGER DEFAULT 0')
        conn.commit()

        # First, handle regular notifications for upcoming tasks
        query = """
            SELECT task_id, task_name, due_date
            FROM tasks
            WHERE completed = 0 
            AND created_by = ?
            AND (
                (notified = 0 AND due_date <= ?) 
                OR 
                (due_date < ? AND telegram_notify = 1)
            )
        """

        c.execute(query, (
            username,
            today,
            today
        ))
        due_tasks = c.fetchall()

        for task in due_tasks:
            task_id = task[0]
            task_name = task[1]
            due_date = task[2]
            
            # Check if task is off-track
            task_due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            is_offtrack = task_due_date < current_date
            
            # For offtrack tasks, check if we already notified today
            if is_offtrack:
                c.execute("""
                    SELECT last_notification_date 
                    FROM tasks 
                    WHERE task_id = ?
                """, (task_id,))
                result = c.fetchone()
                last_notif = result[0] if result and result[0] else None
                
                if last_notif == today:
                    continue  # Skip if already notified today
            
            # Send notification
            send_notification(task_id, task_name, due_date, is_offtrack)
            
            # Update notification tracking
            if is_offtrack:
                # For offtrack tasks, update last notification date
                c.execute("""
                    UPDATE tasks 
                    SET last_notification_date = ? 
                    WHERE task_id = ?
                """, (today, task_id))
            else:
                # For regular notifications, mark as notified
                c.execute("UPDATE tasks SET notified = 1 WHERE task_id = ?", (task_id,))

        # Update user's last notification date
        c.execute("""
            UPDATE users 
            SET last_notification_date = ? 
            WHERE username = ?
        """, (today, username))
        
        conn.commit()
    except Exception as e:
        print(f"Error in check_notifications: {e}")
        conn.rollback()
