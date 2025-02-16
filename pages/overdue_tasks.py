import streamlit as st
from db import get_connection

def show_overdue_tasks():
    st.title("⚠️ Overdue Tasks")
    
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT task_id, task_name, due_date 
        FROM tasks 
        WHERE due_date < date('now') 
        AND completed = 0
    """)
    
    overdue_tasks = c.fetchall()
    
    if not overdue_tasks:
        st.success("🎉 No overdue tasks!")
        return
        
    for task in overdue_tasks:
        task_id, task_name, due_date = task
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{task_name}**")
                st.caption(f"Due: {due_date}")
            with cols[1]:
                if st.button("Mark Complete", key=f"complete_{task_id}"):
                    mark_task_complete(task_id)
                    st.rerun()

def mark_task_complete(task_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
    conn.commit()
