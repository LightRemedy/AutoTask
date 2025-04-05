from datetime import datetime, date

def get_current_date():
    """
    Get the current date, using mock date from session state if available.
    """
    import streamlit as st
    mock_date = st.session_state.get("mock_now")
    
    if mock_date is None:
        return date.today()
    
    if isinstance(mock_date, date):
        return mock_date
    
    if isinstance(mock_date, str):
        try:
            return datetime.strptime(mock_date, '%Y-%m-%d').date()
        except ValueError:
            return date.today()
    
    return date.today()

def format_date(date_obj):
    """Format a date object into YYYY-MM-DD string."""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime('%Y-%m-%d') 