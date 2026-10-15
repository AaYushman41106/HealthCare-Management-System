"""Authentication state and session helpers for Streamlit UI."""
from typing import Optional
import streamlit as st
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


def init_session_state() -> None:
    """Initialize session state defaults."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "full_name" not in st.session_state:
        st.session_state.full_name = None
    if "active_nav" not in st.session_state:
        st.session_state.active_nav = "Dashboard"
    if "show_register" not in st.session_state:
        st.session_state.show_register = False


def login_user(user: User) -> None:
    """Set session state on successful authentication."""
    st.session_state.authenticated = True
    st.session_state.user_id = user.id
    st.session_state.username = user.username
    st.session_state.email = user.email
    st.session_state.role = user.role.value if hasattr(user.role, "value") else str(user.role)
    
    # Resolve full name if available
    if user.role == UserRole.PATIENT and user.patient_profile:
        st.session_state.full_name = user.patient_profile.full_name
    elif user.role == UserRole.DOCTOR and user.doctor_profile:
        st.session_state.full_name = user.doctor_profile.full_name
    else:
        st.session_state.full_name = user.username.title()

    st.session_state.active_nav = "Dashboard"
    st.session_state.show_register = False


def logout_user() -> None:
    """Clear session state on logout."""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.role = None
    st.session_state.full_name = None
    st.session_state.active_nav = "Dashboard"
    st.session_state.show_register = False


def get_current_user(db: Session) -> Optional[User]:
    """Retrieve full User ORM entity from database using session user_id."""
    if not st.session_state.get("authenticated") or not st.session_state.get("user_id"):
        return None
    return db.query(User).filter(User.id == st.session_state.user_id).first()
