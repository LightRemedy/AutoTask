import streamlit as st
from db import get_connection

def show():
    if "current_view_group" not in st.session_state:
        st.error("No group selected")
        return
    
    group_id = st.session_state.current_view_group
    conn = get_connection()
    c = conn.cursor()
    
    # Get group details
    c.execute('SELECT * FROM groups WHERE group_id = ?', (group_id,))
    group = c.fetchone()
    group_id, group_name, created_by, color, remarks = group
    
    # Display group header
    st.button("← Back to Groups", on_click=lambda: st.session_state.pop("current_view_group"))
    st.title(f"📦 {group_name}")
    
    # Group information section
    with st.container(border=True):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f'<div style="background-color: {color}; width: 50px; height: 50px; border-radius: 8px;"></div>', 
                      unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                **Created by:** {created_by}  
                **Remarks:** {remarks or 'No remarks'}
            """)
    
    # Tasks list section
    st.subheader("📋 Tasks in this Group")
    c.execute('SELECT task_id, task_name, due_date, completed FROM tasks WHERE group_id = ? ORDER BY due_date', (group_id,))
    tasks = c.fetchall()
    
    if tasks:
        for task in tasks:
            task_id, task_name, due_date, completed = task
            with st.container(border=True):
                cols = st.columns([8, 2])
                with cols[0]:
                    status = "✅" if completed else "⏳"
                    st.markdown(f"{status} **{task_name}**")
                    st.caption(f"Due: {due_date}")
                with cols[1]:
                    if not completed:
                        if st.button("Mark Complete", key=f"complete_{task_id}"):
                            c.execute("UPDATE tasks SET completed = 1 WHERE task_id = ?", (task_id,))
                            conn.commit()
                            st.rerun()
    else:
        st.info("No tasks found in this group.")
    
    conn.close()
