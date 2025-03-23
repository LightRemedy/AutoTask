#core/notification.py
import streamlit as st
from core.database import get_connection
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


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

def send_telegram_message(message):
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except TelegramError as e:
        st.error(f"Telegram Error: {str(e)}")

# Remove all async/await references
def send_notification(task_id, task_name, due_date):
    message = f"🔔 Task Reminder:\nTask: {task_name}\nDue Date: {due_date}"
    st.info(message)
    send_telegram_message(message)