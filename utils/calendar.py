#utils/calendar.py
from core.database import get_connection


def get_events_for_user(username):
    """
    Fetch tasks created by the user and transform them into
    event format for calendar or list visualisation.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT task_name, due_date, completed
        FROM tasks
        WHERE created_by = ?
    """, (username,))

    rows = c.fetchall()
    events = []

    for name, due, completed in rows:
        events.append({
            "title": f"{'✅' if completed else '🔄'} {name}",
            "start": due,
            "allDay": True,
            "color": "#4CAF50" if completed else "#FF5722"
        })

    conn.close()
    return events
