#modules/overdue.py
import streamlit as st
from core.database import get_connection


def show_overdue_tasks():
    st.title("⚠️ Overdue Tasks")
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT task_id, task_name, due_date
        FROM tasks
        WHERE due_date < date('now') AND completed = 0
    """)

    overdue = c.fetchall()

    if not overdue:
        st.success("🎉 No overdue tasks!")
        return

    for task_id, name, due in overdue:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"Due: {due}")
            with col2:
                if st.button("✅ Mark Complete", key=f"overdue_{task_id}"):
                    c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
                    conn.commit()
                    st.rerun()

    conn.close()
    