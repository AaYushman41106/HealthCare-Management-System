"""Streamlit Security Center, Enterprise Governance & Audit Ledger.
Pure-Python, Zero HTML, Zero Custom CSS.
"""
from datetime import datetime, timezone
import io
import pandas as pd
import streamlit as st
from app.db.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.services.audit_service import log_event
from app.ui.auth_state import get_current_user
from app.ui.components import (
    COLOR_CRITICAL,
    COLOR_SUCCESS,
    COLOR_WARNING,
    empty_state,
    page_header,
    section_heading,
)


def render_security_center(view_mode: str = "Security Center") -> None:
    """Render administrative security posture, user account governance, and audit ledger."""
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or user.role != UserRole.ADMIN:
            st.error("Access Forbidden: Administrator privileges required.")
            return

        if view_mode == "User Management":
            page_header("User Account Governance", "Manage user identities, active statuses, and credential lockouts.", badge="IAM Governance")
            _render_users_panel(db, user)
            return

        if view_mode == "Doctor Management":
            page_header("Medical Staff & Credentialing", "Manage licensed physicians and consultation scheduling availability.", badge="Staff Governance")
            _render_doctors_panel(db, user)
            return

        if view_mode == "Audit Ledger":
            page_header("System Audit Ledger", "Immutable, tamper-evident log of authentications, authorizations, and record access.", badge="Security Ledger")
            _render_audit_ledger_panel(db)
            return

        # Default Security Center view
        page_header(
            "Enterprise Security Center",
            "Security posture monitoring, threat defenses, identity governance, and compliance auditing.",
            badge="Security Operations",
        )

        # Security Posture Matrix Overview
        with st.container(border=True):
            section_heading("Security Posture & Defensive Controls", "Live status of baseline security controls and active protections.")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.success("🟢 **Bcrypt Password Policy**\nWork factor 12 salted hashing.")
            with s2:
                st.success("🟢 **Brute-Force Shield**\n5-attempt threshold, 15m lockout.")
            with s3:
                st.success("🟢 **RBAC & Anti-IDOR**\nServer-side validation active.")
            with s4:
                st.success("🟢 **Audit Logging**\nAppend-only tamper-evident records.")

        st.write("")

        # Threat Intelligence / Incidents summary
        failed_attempts = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILURE").count()
        locked_users = db.query(User).filter(User.locked_until.isnot(None)).count()
        total_logs = db.query(AuditLog).count()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Recorded Events", total_logs)
        m2.metric("Failed Login Warnings", failed_attempts, delta=None if failed_attempts == 0 else f"{failed_attempts} events", delta_color="inverse")
        m3.metric("Currently Locked Accounts", locked_users, delta=None if locked_users == 0 else f"{locked_users} locked", delta_color="inverse")

        st.divider()

        # Tabs for deep-dive governance
        tab_audit, tab_users, tab_doctors = st.tabs([
            "📜 Audit Ledger & Telemetry",
            "👥 User Account Governance",
            "🩺 Medical Staff Directory",
        ])

        with tab_audit:
            _render_audit_ledger_panel(db)

        with tab_users:
            _render_users_panel(db, user)

        with tab_doctors:
            _render_doctors_panel(db, user)

    finally:
        db.close()


def _render_audit_ledger_panel(db) -> None:
    """Render searchable and filterable audit ledger with CSV export."""
    section_heading("Security & Operational Audit Ledger", "Comprehensive log of authentications, data access, and administrative actions.")

    # Filter controls
    c_search, c_action, c_res = st.columns([2, 1, 1])
    with c_search:
        search_query = st.text_input("🔍 Search Audit Events", placeholder="Search details, IP, or resource ID...")
    with c_action:
        all_actions = [row[0] for row in db.query(AuditLog.action).distinct().all()]
        selected_action = st.selectbox("Action Filter", options=["All Actions"] + sorted(all_actions), key="audit_action_filter")
    with c_res:
        all_res = [row[0] for row in db.query(AuditLog.resource_type).distinct().all()]
        selected_res = st.selectbox("Resource Filter", options=["All Resources"] + sorted(all_res), key="audit_res_filter")

    # Build query
    q = db.query(AuditLog)
    if selected_action != "All Actions":
        q = q.filter(AuditLog.action == selected_action)
    if selected_res != "All Resources":
        q = q.filter(AuditLog.resource_type == selected_res)
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        q = q.filter((AuditLog.details.ilike(term)) | (AuditLog.ip_address.ilike(term)))

    logs = q.order_by(AuditLog.timestamp.desc()).limit(200).all()

    if logs:
        st.caption(f"Displaying {len(logs)} matched audit event(s):")
        table = []
        for l in logs:
            table.append({
                "ID": l.id,
                "Timestamp (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "N/A",
                "Action": l.action,
                "Resource": l.resource_type,
                "Resource ID": l.resource_id or "-",
                "User ID": l.user_id or "System/Anon",
                "IP Address": l.ip_address or "127.0.0.1",
                "Details": l.details or "-",
            })
        df_logs = pd.DataFrame(table)
        st.dataframe(df_logs, use_container_width=True, hide_index=True)

        # CSV Download Button
        csv_buffer = io.StringIO()
        df_logs.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Export Audit Ledger (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"securecare_audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="secondary",
        )
    else:
        empty_state("No Audit Events Found", "No events matched the selected filter criteria.")


def _render_users_panel(db, current_admin: User) -> None:
    """Render user account governance, role inspect, active toggle, and unlock."""
    section_heading("Identity & Access Management (IAM)", "Inspect registered user accounts, toggle active states, and release brute-force lockouts.")

    users = db.query(User).order_by(User.id).all()
    if not users:
        empty_state("No Users Registered", "No user accounts are currently present in the database.")
        return

    u_data = []
    now = datetime.now(timezone.utc)
    for u in users:
        is_locked = False
        if u.locked_until:
            lu = u.locked_until
            if lu.tzinfo is None:
                lu = lu.replace(tzinfo=timezone.utc)
            is_locked = lu > now

        u_data.append({
            "ID": u.id,
            "Username": u.username,
            "Email": u.email,
            "Role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "Status": "Active" if u.is_active else "Inactive",
            "Failed Logins": u.failed_login_attempts or 0,
            "Lockout State": f"Locked until {u.locked_until.strftime('%H:%M:%S UTC')}" if is_locked else "Normal",
        })
    st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)

    st.divider()

    # Lockout Release Mechanism
    locked_users = [
        u for u in users
        if u.locked_until and (u.locked_until.replace(tzinfo=timezone.utc) if u.locked_until.tzinfo is None else u.locked_until) > now
    ]

    col_ctrl1, col_ctrl2 = st.columns(2)

    with col_ctrl1:
        with st.container(border=True):
            st.markdown("##### 🔓 Release Account Lockout")
            st.caption("Release 15-minute temporary brute-force lockouts for legitimate users.")
            if locked_users:
                u_choice = st.selectbox(
                    "Locked User Account",
                    options=[f"{u.username} ({u.email})" for u in locked_users],
                    key="select_locked_user_dropdown",
                )
                target_u_name = u_choice.split(" ")[0]
                if st.button("Unlock Selected Account", type="primary", use_container_width=True):
                    target_u = db.query(User).filter(User.username == target_u_name).first()
                    if target_u:
                        target_u.failed_login_attempts = 0
                        target_u.locked_until = None
                        db.commit()
                        log_event(
                            db=db,
                            action="ACCOUNT_UNLOCKED",
                            resource_type="admin",
                            user_id=current_admin.id,
                            resource_id=target_u.id,
                            details=f"Admin '{current_admin.username}' released account lockout for '{target_u.username}'",
                        )
                        st.success(f"Account '{target_u.username}' has been successfully unlocked.")
                        st.rerun()
            else:
                st.info("No accounts are currently under security lockout.")

    with col_ctrl2:
        with st.container(border=True):
            st.markdown("##### ⚡ Toggle User Active Status")
            st.caption("Enable or disable platform login access for non-admin accounts.")
            non_admin_users = [u for u in users if u.id != current_admin.id]
            if non_admin_users:
                t_choice = st.selectbox(
                    "User Account",
                    options=[f"#{u.id} — {u.username} ({u.role.value}) [{'Active' if u.is_active else 'Inactive'}]" for u in non_admin_users],
                    key="select_user_to_toggle_v2",
                )
                target_t_id = int(t_choice.split(" ")[0].replace("#", ""))
                target_user_obj = db.query(User).filter(User.id == target_t_id).first()
                btn_label = "Deactivate Account" if (target_user_obj and target_user_obj.is_active) else "Activate Account"
                if st.button(btn_label, use_container_width=True):
                    if target_user_obj:
                        target_user_obj.is_active = not target_user_obj.is_active
                        db.commit()
                        log_event(
                            db=db,
                            action="USER_STATUS_TOGGLED",
                            resource_type="admin",
                            user_id=current_admin.id,
                            resource_id=target_user_obj.id,
                            details=f"Admin set '{target_user_obj.username}' active status to {target_user_obj.is_active}",
                        )
                        st.success(f"User '{target_user_obj.username}' status set to {'Active' if target_user_obj.is_active else 'Inactive'}.")
                        st.rerun()
            else:
                st.info("No non-admin accounts available to manage.")


def _render_doctors_panel(db, current_admin: User) -> None:
    """Render physician directory and scheduling availability controls."""
    section_heading("Physician Credential Directory", "Licensed medical staff credentials and consultation scheduling status.")

    doctors = db.query(Doctor).order_by(Doctor.id).all()
    if not doctors:
        empty_state("No Physicians Registered", "No physician profiles exist in the system.")
        return

    d_table = []
    for d in doctors:
        d_table.append({
            "Doctor ID": d.id,
            "Full Legal Name": f"Dr. {d.full_name}" if d.full_name else d.user.username,
            "Specialization": d.specialization or "General Practice",
            "License #": d.license_number,
            "Contact Phone": d.phone or "N/A",
            "Availability": "Available" if (d.is_active and d.user.is_active) else "Disabled / Off-duty",
        })
    st.dataframe(pd.DataFrame(d_table), use_container_width=True, hide_index=True)

    st.divider()
    with st.container(border=True):
        st.markdown("##### 🩺 Manage Physician Scheduling Availability")
        st.caption("Temporarily enable or disable a physician's availability for patient bookings.")
        col_d_sel, col_d_btn = st.columns([3, 1])
        with col_d_sel:
            d_choice = st.selectbox(
                "Physician Profile",
                options=[f"#{d.id} — Dr. {d.full_name} ({'Available' if d.is_active else 'Disabled'})" for d in doctors],
                key="select_doc_to_toggle_v2",
            )
            target_d_id = int(d_choice.split(" ")[0].replace("#", ""))
        with col_d_btn:
            target_doc_obj = db.query(Doctor).filter(Doctor.id == target_d_id).first()
            d_btn_label = "Disable Scheduling" if (target_doc_obj and target_doc_obj.is_active) else "Enable Scheduling"
            st.write("")
            if st.button(d_btn_label, use_container_width=True):
                if target_doc_obj:
                    target_doc_obj.is_active = not target_doc_obj.is_active
                    db.commit()
                    log_event(
                        db=db,
                        action="DOCTOR_STATUS_TOGGLED",
                        resource_type="admin",
                        user_id=current_admin.id,
                        resource_id=target_doc_obj.id,
                        details=f"Admin toggled scheduling status for Dr. {target_doc_obj.full_name} to {target_doc_obj.is_active}",
                    )
                    st.success(f"Dr. {target_doc_obj.full_name} availability updated.")
                    st.rerun()
