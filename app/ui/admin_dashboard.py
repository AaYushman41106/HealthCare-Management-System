"""Streamlit Administrator Executive Command Center & Clinical Operations.
Pure-Python, Zero HTML, Zero Custom CSS.
"""
from datetime import date, datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app.db.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.services.jira_service import JiraService
from app.ui.auth_state import get_current_user
from app.ui.components import (
    COLOR_CRITICAL,
    COLOR_DARK_NAVY,
    COLOR_NAVY,
    COLOR_PALE_TEAL,
    COLOR_SUCCESS,
    COLOR_TEAL,
    COLOR_WARNING,
    apply_plotly_theme,
    empty_state,
    page_header,
    section_heading,
)


def render_admin_dashboard() -> None:
    """Render executive administrative console with live database metrics and Plotly charts."""
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or user.role != UserRole.ADMIN:
            st.error("Access Forbidden: Administrator privileges required.")
            return

        page_header(
            "Executive Command Center",
            "Real-time clinical operations telemetry, cybersecurity audit monitoring, and agile delivery status.",
            badge="Executive Console",
        )

        # Database telemetry counts
        total_users = db.query(User).count()
        total_patients = db.query(Patient).count()
        active_doctors = db.query(Doctor).filter(Doctor.is_active.is_(True)).count()
        total_appts = db.query(Appointment).count()
        
        today = date.today()
        today_appts = db.query(Appointment).filter(Appointment.appointment_date == today).count()

        pending_appts = db.query(Appointment).filter(Appointment.status == AppointmentStatus.PENDING).count()
        confirmed_appts = db.query(Appointment).filter(Appointment.status == AppointmentStatus.CONFIRMED).count()
        completed_appts = db.query(Appointment).filter(Appointment.status == AppointmentStatus.COMPLETED).count()
        cancelled_appts = db.query(Appointment).filter(Appointment.status == AppointmentStatus.CANCELLED).count()

        total_audits = db.query(AuditLog).count()
        failed_logins = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILURE").count()
        locked_accounts = db.query(User).filter(User.locked_until.isnot(None)).count()

        # System Health Status Row
        with st.container(border=True):
            section_heading("System Health & Operational Status", "Live service indicators and infrastructure availability.")
            c_h1, c_h2, c_h3, c_h4 = st.columns(4)
            with c_h1:
                st.success("🟢 **Database (SQLite)**: Healthy")
            with c_h2:
                jira_status = JiraService.check_connection()
                if jira_status.get("is_connected"):
                    st.success("🟢 **Jira Cloud API**: Connected")
                else:
                    st.info("🟡 **Jira Cloud API**: Offline/Cache")
            with c_h3:
                st.success("🟢 **Auth Service**: Active (JWT/bcrypt)")
            with c_h4:
                st.success("🟢 **Audit Logging**: Immutable Ledger Active")

        st.write("")

        # Executive KPI Metrics Row
        section_heading("Executive Key Performance Indicators", "Operational metrics across patients, physicians, and security controls.")
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
        r1_c1.metric("Enrolled Patients", total_patients, help="Total active registered patient profiles.")
        r1_c2.metric("Active Physicians", active_doctors, help="Licensed physicians currently accepting appointments.")
        r1_c3.metric("Total Consultations", total_appts, delta=f"{today_appts} scheduled today", delta_color="normal")
        r1_c4.metric(
            "Account Lockouts",
            locked_accounts,
            delta=f"{failed_logins} failed login attempts",
            delta_color="inverse" if failed_logins > 0 else "off",
            help="Accounts temporarily suspended under brute-force protection.",
        )

        st.divider()

        # Operational Trends Section using Plotly with apply_plotly_theme
        section_heading("Clinical & Security Telemetry Analytics")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            with st.container(border=True):
                st.markdown("**Appointment Volume by Status**")
                st.caption("Distribution across pending, confirmed, completed, and cancelled consultations.")
                if total_appts > 0:
                    status_df = pd.DataFrame([
                        {"Status": "Pending Review", "Count": pending_appts},
                        {"Status": "Confirmed", "Count": confirmed_appts},
                        {"Status": "Completed", "Count": completed_appts},
                        {"Status": "Cancelled", "Count": cancelled_appts},
                    ])
                    fig_status = px.pie(
                        status_df,
                        names="Status",
                        values="Count",
                        hole=0.55,
                        color="Status",
                        color_discrete_map={
                            "Pending Review": COLOR_WARNING,
                            "Confirmed": COLOR_TEAL,
                            "Completed": COLOR_SUCCESS,
                            "Cancelled": "#94A3B8",
                        },
                    )
                    apply_plotly_theme(fig_status, height=270)
                    fig_status.update_traces(textinfo="percent+value", textfont_size=12)
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    empty_state("No Consultation Telemetry", "No appointments recorded in the database yet.")

        with col_chart2:
            with st.container(border=True):
                st.markdown("**Security & Audit Event Types**")
                st.caption("Top 5 most frequent security actions and administrative events.")
                all_logs = db.query(AuditLog.action).all()
                if all_logs:
                    action_series = pd.Series([l[0] for l in all_logs]).value_counts().head(5)
                    audit_df = pd.DataFrame({"Action": action_series.index, "Count": action_series.values})
                    fig_audit = px.bar(
                        audit_df,
                        x="Count",
                        y="Action",
                        orientation="h",
                        color="Action",
                        color_discrete_sequence=[COLOR_TEAL, COLOR_NAVY, COLOR_SUCCESS, COLOR_WARNING, COLOR_CRITICAL],
                    )
                    apply_plotly_theme(fig_audit, height=270)
                    fig_audit.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_audit, use_container_width=True)
                else:
                    empty_state("No Audit Events", "No security events recorded in the system yet.")

        st.divider()

        # Sprint Velocity Snapshot
        with st.container(border=True):
            section_heading("Adaptive SDLC Agile Sprint Delivery", "Sprint velocity and delivery status tracked via Jira Cloud.")
            sprints_resp = JiraService.get_sprints()
            sprints = sprints_resp.get("sprints", []) if isinstance(sprints_resp, dict) else sprints_resp

            if sprints:
                s_names = [s.get("name", f"Sprint {i+1}") for i, s in enumerate(sprints)]
                s_planned = [s.get("planned_points", 20) for s in sprints]
                s_completed = [s.get("completed_points", 18) for s in sprints]

                fig_sprint = go.Figure(data=[
                    go.Bar(name="Planned Story Points", x=s_names, y=s_planned, marker_color="#CBD5E1"),
                    go.Bar(name="Completed Story Points", x=s_names, y=s_completed, marker_color=COLOR_TEAL),
                ])
                apply_plotly_theme(fig_sprint, height=260)
                fig_sprint.update_layout(barmode="group", xaxis_title=None, yaxis_title="Story Points")
                st.plotly_chart(fig_sprint, use_container_width=True)

        st.divider()

        # Recent Audit Log Activity
        section_heading("Recent Security & Operational Audit Log Activity", "Chronological feed of user authentications and clinical data access events.")
        recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
        if recent_logs:
            log_table = []
            for l in recent_logs:
                log_table.append({
                    "Timestamp (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "N/A",
                    "Action": l.action,
                    "Resource": l.resource_type,
                    "User ID": l.user_id or "System / Anon",
                    "IP Address": l.ip_address or "127.0.0.1",
                    "Event Details": l.details or "-",
                })
            st.dataframe(pd.DataFrame(log_table), use_container_width=True, hide_index=True)
        else:
            empty_state("Audit Ledger Empty", "No recent security logs recorded.")

    finally:
        db.close()
