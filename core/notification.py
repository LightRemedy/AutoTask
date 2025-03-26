#core/notification.py
import streamlit as st
from core.database import get_connection
import asyncio
from telegram import Bot
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

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

def send_notification(task_id, task_name, due_date):
    """
    Send a notification for the given task via Telegram and display in Streamlit.
    """
    message = f"🔔 Task Reminder:\nTask: {task_name}\nDue Date: {due_date}"
    
    # Display in Streamlit
    st.info(message)
    
    # Send via Telegram
    asyncio.run(send_telegram_message(message))

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
