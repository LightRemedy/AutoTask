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
            username TEXT COLLATE NOCASE PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            email TEXT,
            address TEXT,
            gender TEXT,
            contact TEXT,
            telegram_chat_id TEXT,
            view_preference TEXT DEFAULT 'calendar',
            last_notification_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            category TEXT,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            task_name TEXT,
            description TEXT,
            notification_days INTEGER,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            notified INTEGER DEFAULT 0,
            created_by TEXT,
            recurrence_pattern TEXT,
            recurrence_end_date TEXT,
            telegram_notify INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 1,
            estimated_duration INTEGER,
            actual_duration INTEGER,
            completion_date TEXT,
            last_notification_date TEXT,
            FOREIGN KEY (group_id) REFERENCES groups(group_id),
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT,
            description TEXT,
            created_by TEXT,
            category TEXT,
            default_duration INTEGER,
            FOREIGN KEY(created_by) REFERENCES users(username)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS task_link (
            task_id INTEGER,
            pre_task_id INTEGER,
            link_type TEXT DEFAULT 'prerequisite',
            delay_days INTEGER DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id),
            FOREIGN KEY (pre_task_id) REFERENCES tasks(task_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS task_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            status_change TEXT,
            changed_at TEXT,
            changed_by TEXT,
            notes TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id),
            FOREIGN KEY (changed_by) REFERENCES users(username)
        )
    ''')

    conn.commit()

def insert_presets(conn):
    """Insert sample templates and tasks into the database."""
    c = conn.cursor()
    
    # Check if templates already exist
    c.execute("""
        SELECT group_name 
        FROM groups 
        WHERE isTemplate=1
    """)
    existing_templates = {row[0] for row in c.fetchall()}
    
    # Template definitions
    templates = [
        {
            "name": "Student Unit Enrollment",
            "description": "Template for managing unit enrollment tasks for each teaching period",
            "color": "#4CAF50",
            "category": "academic",
            "recurrence": "quarterly",
            "tasks": [
                {
                    "name": "Check unit prerequisites",
                    "description": "Review academic transcript and check prerequisites for intended units",
                    "days": 60,
                    "duration": 2,
                    "priority": 2
                },
                {
                    "name": "Enroll in units",
                    "description": "Complete unit enrollment through student portal",
                    "days": 30,
                    "duration": 1,
                    "priority": 1
                },
                {
                    "name": "Order required textbooks",
                    "description": "Purchase or order all required textbooks for enrolled units",
                    "days": 14,
                    "duration": 2,
                    "priority": 2
                },
                {
                    "name": "Confirm enrollment",
                    "description": "Verify enrollment status and unit registration",
                    "days": 0,
                    "duration": 1,
                    "priority": 1
                }
            ]
        },
        {
            "name": "Garden Plant Management",
            "description": "Annual garden planting and management schedule",
            "color": "#2196F3",
            "category": "agriculture",
            "recurrence": "yearly",
            "tasks": [
                {
                    "name": "Order seeds for new season",
                    "description": "Select and order seeds for the upcoming planting season",
                    "days": 60,
                    "duration": 3,
                    "priority": 2
                },
                {
                    "name": "Prepare growing site",
                    "description": "Clear area, prepare soil, and set up irrigation",
                    "days": 30,
                    "duration": 5,
                    "priority": 2
                },
                {
                    "name": "Plant seedlings",
                    "description": "Transfer seedlings to prepared growing site",
                    "days": 0,
                    "duration": 2,
                    "priority": 1
                }
            ]
        },
        {
            "name": "Unit Coordinator Tasks",
            "description": "Teaching period preparation and management tasks",
            "color": "#9C27B0",
            "category": "academic",
            "recurrence": "quarterly",
            "tasks": [
                {
                    "name": "Set up LMS sites",
                    "description": "Create and configure Learning Management System sites for units",
                    "days": 60,
                    "duration": 3,
                    "priority": 1
                },
                {
                    "name": "Update ULIGs",
                    "description": "Review and update Unit Learning Information Guides",
                    "days": 45,
                    "duration": 5,
                    "priority": 2
                },
                {
                    "name": "Update lecture content",
                    "description": "Review and update lecture materials and slides",
                    "days": 30,
                    "duration": 10,
                    "priority": 2
                },
                {
                    "name": "Write assignments",
                    "description": "Prepare assignment questions and marking rubrics",
                    "days": 30,
                    "duration": 5,
                    "priority": 2
                },
                {
                    "name": "Set exams",
                    "description": "Create examination papers and solutions",
                    "days": 14,
                    "duration": 5,
                    "priority": 1
                }
            ]
        },
        {
            "name": "Breeding Program Management",
            "description": "Annual livestock breeding program management",
            "color": "#FF9800",
            "category": "agriculture",
            "recurrence": "yearly",
            "tasks": [
                {
                    "name": "Select breeding stock",
                    "description": "Evaluate and select animals for breeding program",
                    "days": 90,
                    "duration": 5,
                    "priority": 1
                },
                {
                    "name": "Group stock for breeding",
                    "description": "Organize selected animals into breeding groups",
                    "days": 60,
                    "duration": 3,
                    "priority": 2
                },
                {
                    "name": "Plan mating schedule",
                    "description": "Create detailed mating timeline and assignments",
                    "days": 45,
                    "duration": 2,
                    "priority": 2
                },
                {
                    "name": "Order husbandry supplies",
                    "description": "Purchase necessary breeding and veterinary supplies",
                    "days": 30,
                    "duration": 2,
                    "priority": 3
                },
                {
                    "name": "Allocate paddocks",
                    "description": "Assign and prepare paddocks for breeding groups",
                    "days": 14,
                    "duration": 3,
                    "priority": 2
                }
            ]
        }
    ]
    
    # Insert templates that don't already exist
    base_date = datetime.date(2026, 1, 1)
    for template in templates:
        if template["name"] not in existing_templates:
            # Create template group
            c.execute("""
                INSERT INTO groups (
                    group_name, remarks, color, category, created_by, isTemplate
                ) VALUES (?,?,?,?,?,?)
            """, (
                template["name"],
                template["description"],
                template["color"],
                template["category"],
                "admin",
                1
            ))
            template_id = c.lastrowid
            
            # Insert tasks
            prev_task_id = None
            for task in template["tasks"]:
                task_due = base_date - datetime.timedelta(days=task["days"])
                c.execute("""
                    INSERT INTO tasks (
                        group_id, task_name, description, notification_days,
                        due_date, recurrence_pattern, recurrence_end_date,
                        priority, estimated_duration, created_by
                    ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (
                    template_id,
                    task["name"],
                    task["description"],
                    task["days"],
                    task_due.isoformat(),
                    template["recurrence"],
                    "2027-12-31",
                    task["priority"],
                    task["duration"],
                    "admin"
                ))
                
                # Create task dependency
                if prev_task_id:
                    c.execute("""
                        INSERT INTO task_link (task_id, pre_task_id, link_type)
                        VALUES (?,?,?)
                    """, (c.lastrowid, prev_task_id, "prerequisite"))
                prev_task_id = c.lastrowid
    
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
