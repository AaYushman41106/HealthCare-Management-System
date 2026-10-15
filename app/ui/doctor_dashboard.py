"""Streamlit Doctor Clinical Workspace — Physician Operational Console."""
from datetime import date
import pandas as pd
import streamlit as st
from fastapi import HTTPException
from app.db.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_record import MedicalRecord
from app.models.user import UserRole
from app.schemas.appointment import AppointmentUpdateRequest
from app.services.appointment_service import update_appointment
from app.ui.auth_state import get_current_user
from app.ui.components import empty_state, page_header, section_heading
from app.ui.medical_records import render_medical_records_list, render_record_authoring_form


def render_doctor_dashboard(view_mode: str = "Clinical Overview") -> None:
    """Render physician workspace with queue management and clinical documentation."""
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or user.role != UserRole.DOCTOR:
            st.error("Access Forbidden: Doctor credentials required.")
            return

        doc = user.doctor_profile
        doc_name = f"Dr. {doc.full_name}" if doc else user.username.title()
        doc_id = doc.id if doc else None

        # Routing based on sidebar navigation
        if view_mode == "Consultation Queue":
            page_header("Consultation Queue", "Review incoming consultation requests and manage approval states.")
            _render_consultation_queue(db, user, doc_id)
            return

        if view_mode == "Schedule":
            page_header("Physician Schedule", "Confirmed clinical consultations ordered chronologically.")
            _render_confirmed_schedule(db, doc_id)
            return

        if view_mode == "Medical Records / Clinical Notes":
            page_header("Clinical Documentation & Prescriptions", "Author diagnostic findings for completed consultations.")
            tab_author, tab_hist = st.tabs(["Author Clinical Record", "Authored History"])
            with tab_author:
                render_record_authoring_form(db, user)
            with tab_hist:
                render_medical_records_list(db, user)
            return

        if view_mode == "Profile":
            page_header("Physician Credential Profile", "Your licensed specialty and medical credential details.")
            if doc:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Full Legal Name:** Dr. {doc.full_name}")
                        st.markdown(f"**Specialization:** {doc.specialization or 'General Practice'}")
                        st.markdown(f"**Medical License #:** `{doc.license_number}`")
                    with c2:
                        st.markdown(f"**Official Email:** `{user.email}`")
                        st.markdown(f"**Contact Phone:** {doc.phone or 'Not specified'}")
                        st.markdown(f"**Clinical Status:** {'Active & Scheduling' if doc.is_active else 'Disabled'}")
            else:
                empty_state("Profile Incomplete", "No physician profile linked to this user account.")
            return

        # Default Clinical Overview
        page_header(f"Clinical Workspace — {doc_name}", f"Specialization: {doc.specialization if doc else 'General Practice'}", badge="Physician Console")

        today = date.today()
        pending_count = db.query(Appointment).filter(Appointment.doctor_id == doc_id, Appointment.status == AppointmentStatus.PENDING).count() if doc_id else 0
        today_count = db.query(Appointment).filter(Appointment.doctor_id == doc_id, Appointment.appointment_date == today).count() if doc_id else 0
        completed_count = db.query(Appointment).filter(Appointment.doctor_id == doc_id, Appointment.status == AppointmentStatus.COMPLETED).count() if doc_id else 0
        confirmed_count = db.query(Appointment).filter(Appointment.doctor_id == doc_id, Appointment.status == AppointmentStatus.CONFIRMED).count() if doc_id else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pending Consultations", pending_count)
        m2.metric("Today's Appointments", today_count)
        m3.metric("Confirmed Upcoming", confirmed_count)
        m4.metric("Completed Consultations", completed_count)

        st.divider()

        # Action Queue
        section_heading("Urgent Patient Requests Requiring Review")
        _render_consultation_queue(db, user, doc_id)

    finally:
        db.close()


def _render_consultation_queue(db, user, doc_id: int):
    """Render consultation queue with action triggers."""
    assigned_appts = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doc_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
        if doc_id
        else []
    )

    if not assigned_appts:
        empty_state("No Consultations Assigned", "You currently have no patient appointments assigned to your queue.", icon="📋")
        return

    # Dataframe summary
    data = []
    for a in assigned_appts:
        data.append({
            "Appt #": a.id,
            "Patient": a.patient.full_name if a.patient else f"Patient #{a.patient_id}",
            "Date": str(a.appointment_date),
            "Time": a.appointment_time,
            "Symptoms / Reason": a.reason,
            "Current Status": a.status.value,
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    # Status action panels
    pending_appts = [a for a in assigned_appts if a.status == AppointmentStatus.PENDING]
    if pending_appts:
        with st.container(border=True):
            st.markdown("##### Action Pending Consultation Requests")
            c_sel, c_conf, c_rej = st.columns([3, 1, 1])
            with c_sel:
                opts = {f"#{a.id} — {a.patient.full_name if a.patient else a.patient_id} ({a.appointment_date} @ {a.appointment_time})": a.id for a in pending_appts}
                sel_lbl = st.selectbox("Select Pending Request", options=list(opts.keys()), label_visibility="collapsed")
                sel_id = opts[sel_lbl]
            with c_conf:
                if st.button("Confirm Consultation", type="primary", use_container_width=True):
                    try:
                        update_appointment(db, user, sel_id, AppointmentUpdateRequest(status=AppointmentStatus.CONFIRMED))
                        st.success(f"Appointment #{sel_id} confirmed.")
                        st.rerun()
                    except HTTPException as e:
                        st.error(e.detail)
            with c_rej:
                if st.button("Reject Request", type="secondary", use_container_width=True):
                    try:
                        update_appointment(db, user, sel_id, AppointmentUpdateRequest(status=AppointmentStatus.REJECTED))
                        st.warning(f"Appointment #{sel_id} rejected.")
                        st.rerun()
                    except HTTPException as e:
                        st.error(e.detail)

    confirmed_appts = [a for a in assigned_appts if a.status == AppointmentStatus.CONFIRMED]
    if confirmed_appts:
        with st.container(border=True):
            st.markdown("##### Complete Confirmed Visit & Proceed to EMR")
            c_sel, c_done = st.columns([3, 2])
            with c_sel:
                opts = {f"#{a.id} — {a.patient.full_name if a.patient else a.patient_id} ({a.appointment_date} @ {a.appointment_time})": a.id for a in confirmed_appts}
                sel_lbl = st.selectbox("Select Confirmed Visit", options=list(opts.keys()), label_visibility="collapsed")
                sel_id = opts[sel_lbl]
            with c_done:
                if st.button("Mark Completed", type="primary", use_container_width=True):
                    try:
                        update_appointment(db, user, sel_id, AppointmentUpdateRequest(status=AppointmentStatus.COMPLETED))
                        st.success(f"Visit #{sel_id} completed. You may now document the clinical record.")
                        st.rerun()
                    except HTTPException as e:
                        st.error(e.detail)


def _render_confirmed_schedule(db, doc_id: int):
    """Render confirmed upcoming consultations chronologically."""
    appts = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doc_id, Appointment.status == AppointmentStatus.CONFIRMED)
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
        .all()
        if doc_id
        else []
    )

    if not appts:
        empty_state("No Confirmed Consultations", "No consultations are currently in CONFIRMED state.", icon="📅")
        return

    for a in appts:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                p_name = a.patient.full_name if a.patient else f"Patient #{a.patient_id}"
                st.markdown(f"**{p_name}**")
                st.caption(f"Reason: {a.reason}")
            with c2:
                st.markdown(f"📅 **{a.appointment_date}**")
                st.caption(f"⏰ {a.appointment_time}")
