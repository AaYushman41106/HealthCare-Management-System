"""Streamlit Patient Portal — Unified Health & Appointments Workspace."""
import streamlit as st
from app.db.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_record import MedicalRecord
from app.models.user import UserRole
from app.ui.appointments import render_appointments_table, render_booking_form, render_doctor_directory
from app.ui.auth_state import get_current_user
from app.ui.components import empty_state, page_header, section_heading
from app.ui.medical_records import render_medical_records_list


def render_patient_dashboard(view_mode: str = "Overview") -> None:
    """Render the patient portal tailored to the selected workflow."""
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or user.role != UserRole.PATIENT:
            st.error("Access Forbidden: Patient credentials required.")
            return

        patient = user.patient_profile
        patient_name = patient.full_name if patient else user.username.title()
        patient_id = patient.id if patient else None

        # Routing based on sidebar navigation
        if view_mode == "Find Doctors":
            page_header("Find Specialists", "Discover board-certified physicians available for consultations.")
            render_doctor_directory(db, user)
            return

        if view_mode == "Book Appointment":
            page_header("Schedule Appointment", "Reserve a clinical consultation with your selected specialist.")
            render_booking_form(db, user)
            return

        if view_mode == "My Appointments":
            page_header("My Consultations", "Review your upcoming consultation itinerary and historical records.")
            render_appointments_table(db, user)
            return

        if view_mode == "Medical Records":
            page_header("Electronic Medical Records (EMR)", "Confidential diagnoses, care instructions, and authorized prescriptions.")
            render_medical_records_list(db, user)
            return

        if view_mode == "Profile":
            page_header("Patient Demographic Profile", "Your registered clinical demographic and contact record.")
            if patient:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Full Legal Name:** {patient.full_name}")
                        st.markdown(f"**Registered Email:** `{user.email}`")
                        st.markdown(f"**Date of Birth:** {patient.date_of_birth or 'Not specified'}")
                    with c2:
                        st.markdown(f"**Gender:** {patient.gender or 'Not specified'}")
                        st.markdown(f"**Phone Number:** {patient.phone or 'Not specified'}")
                        st.markdown(f"**Address:** {patient.address or 'Not specified'}")
            else:
                empty_state("Profile Incomplete", "No demographic record is currently linked to this user account.")
            return

        # Default Overview
        page_header(f"Welcome back, {patient_name}", "Manage your appointments and health records in one place.", badge="Patient Portal")

        # Metric cards
        total_appts = db.query(Appointment).filter(Appointment.patient_id == patient_id).count() if patient_id else 0
        upcoming_appts = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            )
            .count()
            if patient_id
            else 0
        )
        completed_appts = (
            db.query(Appointment)
            .filter(Appointment.patient_id == patient_id, Appointment.status == AppointmentStatus.COMPLETED)
            .count()
            if patient_id
            else 0
        )
        total_records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).count() if patient_id else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Upcoming Appointments", upcoming_appts)
        m2.metric("Total Appointments", total_appts)
        m3.metric("Completed Consultations", completed_appts)
        m4.metric("Medical Records", total_records)

        st.divider()

        # Next upcoming appointment highlight
        section_heading("Next Scheduled Consultation")
        next_appt = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_id,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            )
            .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
            .first()
            if patient_id
            else None
        )

        if next_appt:
            with st.container(border=True):
                col_info, col_status = st.columns([3, 1])
                with col_info:
                    doc_title = f"Dr. {next_appt.doctor.full_name}" if next_appt.doctor else f"Physician #{next_appt.doctor_id}"
                    st.markdown(f"### {doc_title}")
                    st.caption(f"Specialization: **{next_appt.doctor.specialization if next_appt.doctor else 'General Practice'}**")
                    st.markdown(f"📅 **{next_appt.appointment_date}** at **{next_appt.appointment_time}**")
                    st.caption(f"Reason: {next_appt.reason}")
                with col_status:
                    if next_appt.status == AppointmentStatus.CONFIRMED:
                        st.success("Confirmed")
                    else:
                        st.warning("Pending Review")
        else:
            empty_state("No Upcoming Visits", "You do not have any consultations currently scheduled.", icon="📅")

        st.divider()

        # Quick action tabs
        tab_book, tab_all, tab_emr = st.tabs(["Schedule New Visit", "Recent Consultations", "Recent EMR Records"])
        with tab_book:
            render_booking_form(db, user)
        with tab_all:
            render_appointments_table(db, user)
        with tab_emr:
            render_medical_records_list(db, user)

    finally:
        db.close()
