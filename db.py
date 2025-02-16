import sqlite3
import datetime

DATABASE_NAME = 'task_manager.db'

def get_connection():
    return sqlite3.connect(DATABASE_NAME, check_same_thread=False)

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
            contact TEXT
        )
    ''')

    # Groups table (new)
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            created_by TEXT,
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
    c.execute("SELECT COUNT(*) FROM templates")
    count = c.fetchone()[0]
    if count == 0:
        # Insert preset templates
        c.execute("INSERT INTO templates (template_name, created_by) VALUES (?,?)",
                  ("Primary/Secondary School", "admin"))
        primary_template_id = c.lastrowid
        c.execute("INSERT INTO templates (template_name, created_by) VALUES (?,?)",
                  ("Enrollment for Uni", "admin"))
        enrollment_template_id = c.lastrowid

        # Preset due dates and tasks
        school_due_date = datetime.date(2026, 1, 1)
        primary_tasks = [
            ("Reminder: Buy textbooks for next year", 60, (school_due_date - datetime.timedelta(days=60)).strftime('%Y-%m-%d')),
            ("Task: Buy textbooks", 30, (school_due_date - datetime.timedelta(days=30)).strftime('%Y-%m-%d')),
            ("Reminder: Buy reminder", 14, (school_due_date - datetime.timedelta(days=14)).strftime('%Y-%m-%d')),
            ("D-Day: Buy textbooks", 0, school_due_date.strftime('%Y-%m-%d'))
        ]
        for task in primary_tasks:
            c.execute(
                "INSERT INTO tasks (template_id, task_name, notification_days, due_date) VALUES (?,?,?,?)",
                (primary_template_id, task[0], task[1], task[2])
            )

        enrollment_due_date = datetime.date(2026, 1, 1)
        enrollment_tasks = [
            ("Reminder: Enroll for your course (30 days before)", 30, (enrollment_due_date - datetime.timedelta(days=30)).strftime('%Y-%m-%d')),
            ("Reminder: Enroll for your course (14 days before)", 14, (enrollment_due_date - datetime.timedelta(days=14)).strftime('%Y-%m-%d')),
            ("Reminder: Enroll for your course (7 days before)", 7, (enrollment_due_date - datetime.timedelta(days=7)).strftime('%Y-%m-%d')),
            ("On Enrollment Day: Enroll for your course", 0, enrollment_due_date.strftime('%Y-%m-%d')),
            ("Reminder: Email if you want to change course or withdraw (14 days before)", 14, (enrollment_due_date - datetime.timedelta(days=14)).strftime('%Y-%m-%d')),
            ("Reminder: Email if you want to change course or withdraw (7 days before)", 7, (enrollment_due_date - datetime.timedelta(days=7)).strftime('%Y-%m-%d'))
        ]
        for task in enrollment_tasks:
            c.execute(
                "INSERT INTO tasks (template_id, task_name, notification_days, due_date) VALUES (?,?,?,?)",
                (enrollment_template_id, task[0], task[1], task[2])
            )
        conn.commit()
