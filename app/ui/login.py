"""Streamlit Login Page — Premium Healthcare SaaS Experience.
Pure-Python, Zero HTML, Zero Custom CSS.
"""
from typing import Optional
import streamlit as st
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.services.audit_service import log_event
from app.services.auth_service import AuthService
from app.ui.auth_state import login_user


def _switch_persona(role: UserRole, preferred_username: Optional[str] = None) -> None:
    """Instantly switch persona for demonstration and role boundary evaluation."""
    db = SessionLocal()
    try:
        q = db.query(User).filter(User.role == role, User.is_active.is_(True))
        user = None
        if preferred_username:
            user = q.filter(User.username == preferred_username).first()
        if not user:
            user = q.first()

        if user:
            # Clear lockout if any
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

            # Record audit event for compliance
            log_event(
                db=db,
                action="LOGIN_SUCCESS",
                resource_type="auth",
                user_id=user.id,
                details=f"Development Persona Switcher sign-in ({role.value}: {user.username})",
            )
            login_user(user)
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(f"No active account found for role {role.value} in the database.")
    finally:
        db.close()


def render_login_page() -> None:
    """Render an elegant, professional healthcare sign-in experience."""
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("# SecureCare")
        st.markdown("### Healthcare, connected and protected.")
        st.caption("Adaptive Secure SDLC Framework — High-Assurance Clinical & Administrative Portal")
        st.divider()

        with st.container(border=True):
            st.markdown("#### Sign In")
            st.caption("Enter your clinical or administrative credentials to access your secure portal.")

            with st.form("securecare_sign_in_form"):
                username_or_email = st.text_input(
                    "Username or Work Email",
                    placeholder="admin, priya.sharma@securecare.local, or email",
                    key="login_user_input",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your confidential password",
                    key="login_pass_input",
                )
                submit_btn = st.form_submit_button(
                    "Access SecureCare Portal",
                    type="primary",
                    use_container_width=True,
                )

            if submit_btn:
                if not username_or_email or not password:
                    st.warning("Please provide both your identifier and password.")
                else:
                    db = SessionLocal()
                    try:
                        user, err_msg = AuthService.authenticate_user(
                            db=db,
                            username_or_email=username_or_email.strip(),
                            password=password,
                            client_ip="127.0.0.1",
                        )
                        if user:
                            login_user(user)
                            st.success(f"Authentication verified. Welcome, {st.session_state.full_name}!")
                            st.rerun()
                        else:
                            st.error(err_msg or "Invalid credentials provided.")
                    finally:
                        db.close()

            st.divider()

            col_reg, col_help = st.columns([1, 1])
            with col_reg:
                st.caption("New to SecureCare?")
                if st.button("Register as Patient", use_container_width=True, type="secondary"):
                    st.session_state.show_register = True
                    st.rerun()

            with col_help:
                st.caption("Access Guidance")
                st.caption("Patients may self-register. Medical staff and administrator credentials are provisioned by enterprise security.")

        # Reassurance Footer
        with st.container(border=True):
            st.caption("🛡️ **Enterprise Security Architecture**")
            st.caption(
                "Encrypted with salted password hashing (12 bcrypt rounds), strict role-based access control, "
                "and progressive brute-force lockout defenses."
            )

        # Non-intrusive collapsible developer persona switcher for evaluation
        with st.expander("🛠️ Development Persona Switcher", expanded=True):
            st.caption("One-click evaluation shortcuts to switch personas and test role boundaries:")

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🛡️ Admin Persona", use_container_width=True, key="btn_persona_admin"):
                    _switch_persona(UserRole.ADMIN)
            with c2:
                if st.button("🩺 Physician Persona", use_container_width=True, key="btn_persona_doctor"):
                    _switch_persona(UserRole.DOCTOR)
            with c3:
                if st.button("👤 Patient Persona", use_container_width=True, key="btn_persona_patient"):
                    _switch_persona(UserRole.PATIENT)

            st.divider()
            st.markdown("**Registered Account Credentials for Manual Sign-In:**")
            st.markdown("""
            * **Administrator**: `admin` or `admin@securecare.org` (Password: `AdminSecure123!`)
            * **Physician (Cardiology)**: `dr_priya` or `priya.sharma@securecare.local` (Password: `DoctorSecure123!`)
            * **Patient**: `manual_patient` or `manual_patient@testcare.org` (Password: `PatientSecure123!`)
            """)
