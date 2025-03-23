import sqlite3
import datetime
import streamlit as st

DATABASE_NAME = 'task_manager.db'

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    return conn

def create_tables(conn):
    c = conn.cursor()

    # Users table (added email field)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            email TEXT,
            address TEXT,
            gender TEXT,
            contact TEXT,
            view_preference TEXT DEFAULT 'calendar'
        )
    ''')

    # Groups table (new)
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            created_by TEXT,
            color TEXT,
            remarks TEXT,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
    ''')

    # Tasks table (modified to include group_id and created_by)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            task_name TEXT,
            notification_days INTEGER,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            notified INTEGER DEFAULT 0,
            created_by TEXT,
            FOREIGN KEY (group_id) REFERENCES groups(group_id),
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
    ''')

    # Templates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT,
            created_by TEXT,
            FOREIGN KEY(created_by) REFERENCES users(username)
        )
    ''')

    conn.commit()


def insert_presets(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups WHERE isTemplate=1")
    if c.fetchone()[0] == 0:
        # Insert as template groups
        templates = [
            ("School Template", "#3498db"),
            ("University Template", "#e74c3c")
        ]
        
        for name, color in templates:
            c.execute('''
                INSERT INTO groups 
                (group_name, color, isTemplate, created_by)
                VALUES (?,?,?,?)
            ''', (name, color, 1, "admin"))
            group_id = c.lastrowid
            
            # Add template tasks
            tasks = [
                ("Buy textbooks", 30, datetime.date(2025, 1, 1).toordinal()),
                ("Submit forms", 7, datetime.date(2025, 1, 15).toordinal())
            ]
            for task in tasks:
                c.execute('''
                    INSERT INTO tasks 
                    (group_id, task_name, notification_days, due_date)
                    VALUES (?,?,?,?)
                ''', (group_id, task[0], task[1], task[2]))
        conn.commit()


def get_group_color(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT color FROM groups WHERE group_id=?", (group_id,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        return "#8E44AD"

def get_task_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total_tasks = c.fetchone()[0]
    return completed_tasks, total_tasks
