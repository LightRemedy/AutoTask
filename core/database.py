#core/database.py
import sqlite3
import datetime

DATABASE_NAME = 'task_manager.db'

def get_connection():
    """Establish and return a connection to the SQLite database."""
    return sqlite3.connect(DATABASE_NAME, check_same_thread=False)

def create_tables(conn):
    """Create necessary tables for users, groups, tasks, templates, and links."""
    c = conn.cursor()

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

    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            created_by TEXT,
            color TEXT,
            remarks TEXT,
            isTemplate INTEGER DEFAULT 0,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
    ''')

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
            template_id INTEGER,
            FOREIGN KEY (group_id) REFERENCES groups(group_id),
            FOREIGN KEY (created_by) REFERENCES users(username),
            FOREIGN KEY (template_id) REFERENCES templates(template_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT,
            created_by TEXT,
            FOREIGN KEY(created_by) REFERENCES users(username)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS task_link (
            task_id INTEGER,
            pre_task_id INTEGER,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id),
            FOREIGN KEY (pre_task_id) REFERENCES tasks(task_id)
        )
    ''')

    conn.commit()

def insert_presets(conn):
    """Insert sample templates and tasks into the database."""
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM templates")
    if c.fetchone()[0] > 0:
        return

    c.execute("INSERT INTO templates (template_name, created_by) VALUES (?,?)",
              ("Primary/Secondary School", "admin"))
    school_template_id = c.lastrowid

    c.execute("INSERT INTO templates (template_name, created_by) VALUES (?,?)",
              ("Enrollment for Uni", "admin"))
    uni_template_id = c.lastrowid

    school_due = datetime.date(2026, 1, 1)
    school_tasks = [
        ("Reminder: Buy textbooks", 60, (school_due - datetime.timedelta(days=60)).isoformat()),
        ("Task: Purchase textbooks", 30, (school_due - datetime.timedelta(days=30)).isoformat()),
        ("Final Reminder", 14, (school_due - datetime.timedelta(days=14)).isoformat()),
        ("D-Day", 0, school_due.isoformat())
    ]

    for name, days, due in school_tasks:
        c.execute("INSERT INTO tasks (template_id, task_name, notification_days, due_date) VALUES (?,?,?,?)",
                  (school_template_id, name, days, due))

    uni_due = datetime.date(2026, 1, 1)
    uni_tasks = [
        ("Reminder: Enrol (30 days)", 30, (uni_due - datetime.timedelta(days=30)).isoformat()),
        ("Reminder: Enrol (14 days)", 14, (uni_due - datetime.timedelta(days=14)).isoformat()),
        ("Reminder: Enrol (7 days)", 7, (uni_due - datetime.timedelta(days=7)).isoformat()),
        ("Enrolment Day", 0, uni_due.isoformat()),
        ("Reminder: Course change (14 days)", 14, (uni_due - datetime.timedelta(days=14)).isoformat()),
        ("Reminder: Course change (7 days)", 7, (uni_due - datetime.timedelta(days=7)).isoformat())
    ]

    for name, days, due in uni_tasks:
        c.execute("INSERT INTO tasks (template_id, task_name, notification_days, due_date) VALUES (?,?,?,?)",
                  (uni_template_id, name, days, due))

    conn.commit()

def get_group_colour(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT color FROM groups WHERE group_id=?", (group_id,))
    result = c.fetchone()
    return result[0] if result else "#8E44AD"

def get_task_completion_count(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=? AND completed=1", (group_id,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE group_id=?", (group_id,))
    total = c.fetchone()[0]
    return completed, total
