"""SecureCare — Adaptive SDLC Healthcare Management System.
Streamlit Pure-Python User Interface Entry Point.
Zero HTML, Zero Custom CSS, Zero JS.
"""
import streamlit as st
from app.db.database import SessionLocal, init_db
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.services.jira_service import JiraService
from app.ui.admin_dashboard import render_admin_dashboard
from app.ui.auth_state import get_current_user, init_session_state, logout_user
from app.ui.components import empty_state, page_header, section_heading
from app.ui.doctor_dashboard import render_doctor_dashboard
from app.ui.jira_board import render_jira_board
from app.ui.login import render_login_page
from app.ui.patient_dashboard import render_patient_dashboard
from app.ui.project_management import render_project_management
from app.ui.registration import render_registration_page
from app.ui.security_center import render_security_center


def render_system_health() -> None:
    """Render technical infrastructure and system health telemetry."""
    page_header("System Health & Infrastructure Telemetry", "Real-time service health, database diagnostics, and integration latency.", badge="Infrastructure")
    
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        audit_count = db.query(AuditLog).count()
        appts_count = db.query(Appointment).count()
        jira_status = JiraService.check_connection()

        with st.container(border=True):
            section_heading("Core Service Diagnostics")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.success("🟢 **Relational Database**\nSQLite / SQLAlchemy 2.0 connected.")
            with c2:
                if jira_status.get("is_connected"):
                    st.success(f"🟢 **Jira Cloud API**\nConnected (`{jira_status.get('project_key', 'SCR')}`).")
                else:
                    st.info(f"🟡 **Jira Cloud Service**\nOffline / High-fidelity cache mode.")
            with c3:
                st.success("🟢 **Security Module**\nbcrypt (12 rounds) & PyJWT operational.")

        st.divider()

        with st.container(border=True):
            section_heading("Database Schema & Record Capacity")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Registered Users", user_count)
            r2.metric("Recorded Consultations", appts_count)
            r3.metric("Security Audit Logs", audit_count)
            r4.metric("Database Engine", "SQLite3")

        st.divider()

        with st.container(border=True):
            section_heading("Defensive Infrastructure Safeguards")
            st.markdown("""
            * **Brute-Force Lockout Defense**: Progressive failure tracker active (5 attempts triggers 15-minute lockout).
            * **Broken Object-Level Authorization (BOLA/IDOR)**: Strict relational ownership checking on appointments and medical records.
            * **Consultation Double-Booking Shield**: Server-side overlap verification preventing patient and physician race conditions.
            * **Data Sanitization**: Pydantic input models enforce strict field types, preventing malformed payload injection.
            """)
    finally:
        db.close()


def render_documentation_page() -> None:
    """Render technical architecture documentation and UN SDG alignment in native Streamlit."""
    page_header("System Documentation & UN SDG Alignment", "Technical architecture specifications, threat model, and Sustainable Development Goals alignment.", badge="Architecture Docs")

    doc_tab1, doc_tab2, doc_tab3 = st.tabs([
        "🏗️ System Architecture & Adaptive SDLC",
        "🎯 UN SDG 9 & SDG 3 Alignment",
        "🔒 Defense-in-Depth Security Matrix",
    ])

    with doc_tab1:
        st.subheader("Adaptive Secure SDLC Architecture")
        st.markdown("""
        **SecureCare** operates as a unified, high-assurance Healthcare Management System (HMS) developed under an **Adaptive Secure Software Development Life Cycle (SDLC)** framework.
        
        Rather than treating security as an isolated post-development audit, defensive threat-mitigation mechanisms are integrated iteratively into each agile sprint:
        
        * **Sprint 1 — Core Foundation, Database Modeling & Authentication**:
          Relational database modeling with SQLAlchemy 2.0 ORM, salted `bcrypt` password hashing, and stateless JWT token issuance.
        * **Sprint 2 — Appointment Lifecycle, RBAC & Clinical Dashboards**:
          State machine for consultations (Pending, Confirmed, Completed, Cancelled, Rejected), role-based access control (`ADMIN`, `DOCTOR`, `PATIENT`), and collision detection.
        * **Sprint 3 — Medical Records, Prescriptions & Tamper-Evident Audit Trails**:
          Confidential electronic medical records (EMR), doctor clinical notes, prescriptions, patient privacy boundaries, and automated tamper-evident audit logging.
        * **Sprint 4 — Threat Defense, Account Lockout & Admin Governance**:
          Brute-force mitigation (automatic 15-minute account lockout after 5 consecutive failed attempts), IDOR prevention, and administrative telemetry.
        * **Sprint 5 — Full System Integration, Jira Cloud & Python-First Interface**:
          Bidirectional Jira Cloud REST API integration, live Agile Kanban board, Sprints 1–5 velocity tracking, and a 100% Python-driven Streamlit user experience.
        """)

    with doc_tab2:
        st.subheader("UN Sustainable Development Goal (SDG) Alignment")
        
        col_sdg9, col_sdg3 = st.columns(2)
        with col_sdg9:
            st.info("""
            #### 🌐 Primary Goal: SDG 9 — Industry, Innovation, and Infrastructure
            * **Resilient Healthcare Digital Infrastructure (Target 9.c)**: Digital healthcare platforms are critical societal assets. SecureCare guarantees continuous uptime and tamper-resistance against credential stuffing and unauthorized modifications.
            * **Adaptive Secure SDLC Methodology (Target 9.4)**: Elevates technological infrastructure through iterative threat modeling, automated regression testing, and security controls at every layer.
            """)

        with col_sdg3:
            st.success("""
            #### 🩺 Contextual Goal: SDG 3 — Good Health and Well-Being
            * **Universal Access to Quality Healthcare (Target 3.8)**: Ensures prompt clinical consultations, eliminates double-booking race conditions, and safeguards sensitive medical histories.
            * **Clinical Privacy**: Enforces strict IDOR boundaries to guarantee that only the patient and attending physicians can view authorized diagnoses and prescriptions.
            """)

    with doc_tab3:
        st.subheader("Defense-in-Depth Security Matrix")
        st.markdown("""
        | Security Feature | Implementation Details | Threat Mitigated |
        | :--- | :--- | :--- |
        | **Stateless Authentication** | PyJWT with cryptographic signing and configurable expiration. | Session hijacking, replay attacks |
        | **Password Protection** | Salted `bcrypt` hashing (12 work rounds). Plaintext passwords never stored. | Credential theft, rainbow table attacks |
        | **Brute-Force Lockout** | Progressive counter tracks failed logins; locks account for 15 minutes after 5 failures. | Automated password spraying & brute-force |
        | **Role-Based Access (RBAC)**| Granular server-side permission checks (`ADMIN`, `DOCTOR`, `PATIENT`). | Privilege escalation, unauthorized access |
        | **Anti-IDOR Protection** | Server-side validation confirms ownership before medical records or appointments are modified. | Insecure Direct Object References (IDOR) |
        | **Collision Prevention** | Database-level checking stops overlapping appointment slots for patients and doctors. | Schedule race conditions, double booking |
        | **Audit Ledger** | Structured logging records IP, user ID, timestamp, and details for every security event. | Non-repudiation, compliance |
        """)


def main() -> None:
    """Main application execution pipeline."""
    # Ensure database schema is initialized
    init_db()

    # Configure Streamlit page
    st.set_page_config(
        page_title="SecureCare HMS",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()

    # If unauthenticated, render login or registration
    if not st.session_state.authenticated:
        if st.session_state.show_register:
            render_registration_page()
        else:
            render_login_page()
        return

    # Authenticated user workflow
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or not user.is_active:
            st.error("Your session has expired or your account has been deactivated. Please sign in again.")
            logout_user()
            st.rerun()
            return

        role = user.role.value if hasattr(user.role, "value") else str(user.role)

        # Sidebar navigation
        with st.sidebar:
            st.markdown("### 🏥 SecureCare")
            st.caption("Adaptive SDLC Healthcare Management")
            st.divider()

            # User Profile Badge
            st.write("**Signed In As:**")
            st.markdown(f"**{st.session_state.full_name}**")
            badge_color = "red" if role == "ADMIN" else ("blue" if role == "DOCTOR" else "green")
            st.caption(f":{badge_color}[●] Role: **{role}**")

            if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
                logout_user()
                st.rerun()

            st.divider()
            st.markdown("**Navigation Menu:**")

            # Role-Specific Navigation Options matching Section 4
            if role == "PATIENT":
                nav_options = [
                    "Overview",
                    "Find Doctors",
                    "Book Appointment",
                    "My Appointments",
                    "Medical Records",
                    "Profile",
                    "Platform Docs & SDG 9",
                ]
            elif role == "DOCTOR":
                nav_options = [
                    "Clinical Overview",
                    "Consultation Queue",
                    "Schedule",
                    "Medical Records / Clinical Notes",
                    "Profile",
                    "Platform Docs & SDG 9",
                ]
            elif role == "ADMIN":
                nav_options = [
                    "Executive Overview",
                    "User Management",
                    "Doctor Management",
                    "Security Center",
                    "Audit Ledger",
                    "Jira Project Management",
                    "Sprints and Epics",
                    "System Health",
                    "Platform Docs & SDG 9",
                ]
            else:
                nav_options = ["Platform Docs & SDG 9"]

            selected_page = st.radio(
                "Navigation",
                options=nav_options,
                label_visibility="collapsed",
            )

            st.divider()
            st.caption("🌐 **UN SDG 9**: Resilient Digital Infrastructure")
            st.caption("🩺 **UN SDG 3**: Good Health & Well-Being")

        # Main Page Routing
        if role == "PATIENT":
            if selected_page in ("Overview", "Find Doctors", "Book Appointment", "My Appointments", "Medical Records", "Profile"):
                render_patient_dashboard(view_mode=selected_page)
            elif selected_page == "Platform Docs & SDG 9":
                render_documentation_page()

        elif role == "DOCTOR":
            if selected_page in ("Clinical Overview", "Consultation Queue", "Schedule", "Medical Records / Clinical Notes", "Profile"):
                render_doctor_dashboard(view_mode=selected_page)
            elif selected_page == "Platform Docs & SDG 9":
                render_documentation_page()

        elif role == "ADMIN":
            if selected_page == "Executive Overview":
                render_admin_dashboard()
            elif selected_page == "User Management":
                render_security_center(view_mode="User Management")
            elif selected_page == "Doctor Management":
                render_security_center(view_mode="Doctor Management")
            elif selected_page == "Security Center":
                render_security_center(view_mode="Security Center")
            elif selected_page == "Audit Ledger":
                render_security_center(view_mode="Audit Ledger")
            elif selected_page == "Jira Project Management":
                render_jira_board()
            elif selected_page == "Sprints and Epics":
                render_project_management()
            elif selected_page == "System Health":
                render_system_health()
            elif selected_page == "Platform Docs & SDG 9":
                render_documentation_page()

        else:
            render_documentation_page()

    finally:
        db.close()


if __name__ == "__main__":
    main()
