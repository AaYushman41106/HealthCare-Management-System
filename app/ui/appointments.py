"""Appointment Management — Modern Patient & Clinical Booking Primitives."""
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreateRequest, AppointmentUpdateRequest
from app.services.appointment_service import (
    create_appointment,
    get_appointments_for_user,
    get_available_doctors,
    update_appointment,
)
from app.ui.components import empty_state, section_heading


def render_doctor_directory(db: Session, current_user: User) -> None:
    """Render a clean, professional medical specialist directory."""
    section_heading("Medical Specialist Directory", "Licensed healthcare professionals currently accepting consultations.")
    doctors = get_available_doctors(db)

    if not doctors:
        empty_state("No Physicians Available", "There are currently no active physicians accepting new consultations.")
        return

    for doc in doctors:
        with st.container(border=True):
            col_avatar, col_info, col_act = st.columns([1, 4, 2])
            with col_avatar:
                st.markdown("🩺")
            with col_info:
                st.markdown(f"**Dr. {doc.full_name or doc.user.username}**")
                st.caption(f"Specialization: **{doc.specialization or 'General Practice'}** | Medical License: `{doc.license_number}`")
                if doc.phone:
                    st.caption(f"Contact: {doc.phone}")
            with col_act:
                st.success("Available for Scheduling")


def render_booking_form(db: Session, current_user: User) -> None:
    """Render guided appointment booking form with conflict detection."""
    section_heading("Schedule a Consultation", "Select an attending specialist, preferred consultation date, and available time slot.")

    doctors = get_available_doctors(db)
    if not doctors:
        empty_state("Scheduling Unavailable", "No physicians are currently active for booking.")
        return

    doctor_map = {
        f"Dr. {doc.full_name or doc.user.username} — {doc.specialization or 'General Practice'}": doc.id
        for doc in doctors
    }

    with st.container(border=True):
        with st.form("book_appointment_form"):
            selected_doc_label = st.selectbox("Attending Physician *", options=list(doctor_map.keys()))
            selected_doc_id = doctor_map[selected_doc_label]

            col_d, col_t = st.columns(2)
            with col_d:
                appt_date = st.date_input(
                    "Consultation Date *",
                    value=date.today() + timedelta(days=1),
                    min_value=date.today(),
                )
            with col_t:
                appt_time = st.selectbox(
                    "Standard Time Slot *",
                    options=[
                        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                        "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
                    ],
                )

            reason = st.text_area(
                "Primary Symptoms or Consultation Purpose *",
                placeholder="Briefly describe the medical concerns, onset of symptoms, or routine checkup details...",
            )

            st.caption("ℹ️ Our server validates physician availability in real time to prevent schedule overlap.")
            submit_btn = st.form_submit_button("Confirm & Reserve Consultation", type="primary", use_container_width=True)

        if submit_btn:
            if not reason or not reason.strip():
                st.warning("Please provide a reason or medical summary for the consultation.")
            else:
                try:
                    payload = AppointmentCreateRequest(
                        doctor_id=selected_doc_id,
                        appointment_date=appt_date,
                        appointment_time=appt_time,
                        reason=reason.strip(),
                    )
                    appt = create_appointment(db=db, current_user=current_user, payload=payload)
                    st.success(f"Consultation successfully confirmed! Appointment ID: #{appt.id} on {appt_date} at {appt_time}.")
                    st.rerun()
                except HTTPException as e:
                    if e.status_code == 409:
                        st.error(f"⚠️ Schedule Conflict (409): {e.detail}")
                    else:
                        st.error(f"Booking Error: {e.detail}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")


def render_appointments_table(db: Session, current_user: User) -> None:
    """Render appointment ledger with clean status badges and patient cancellation."""
    appointments = get_appointments_for_user(db, current_user)
    if not appointments:
        empty_state("No Consultations on Record", "You currently have no scheduled or historical appointments.")
        return

    table_data = []
    for appt in appointments:
        doc_name = f"Dr. {appt.doctor.full_name}" if appt.doctor else f"Physician #{appt.doctor_id}"
        patient_name = appt.patient.full_name if appt.patient else f"Patient #{appt.patient_id}"
        table_data.append({
            "Appt #": appt.id,
            "Date": str(appt.appointment_date),
            "Time": appt.appointment_time,
            "Physician": doc_name,
            "Patient": patient_name,
            "Symptoms / Purpose": appt.reason,
            "Status": appt.status.value,
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Patient cancellation controls for PENDING appointments
    if current_user.role == UserRole.PATIENT:
        pending_appts = [a for a in appointments if a.status == AppointmentStatus.PENDING]
        if pending_appts:
            with st.container(border=True):
                st.markdown("##### Cancel an Upcoming Pending Consultation")
                st.caption("Only appointments in PENDING status can be cancelled by the patient.")
                col_sel, col_btn = st.columns([3, 1])
                with col_sel:
                    options = {
                        f"#{a.id} on {a.appointment_date} @ {a.appointment_time} with Dr. {a.doctor.full_name if a.doctor else a.doctor_id}": a.id
                        for a in pending_appts
                    }
                    selected_label = st.selectbox("Select Consultation", options=list(options.keys()), label_visibility="collapsed")
                    target_id = options[selected_label]
                with col_btn:
                    if st.button("Cancel Booking", type="secondary", use_container_width=True):
                        try:
                            update_appointment(
                                db=db,
                                current_user=current_user,
                                appointment_id=target_id,
                                payload=AppointmentUpdateRequest(status=AppointmentStatus.CANCELLED),
                            )
                            st.success(f"Appointment #{target_id} has been cancelled.")
                            st.rerun()
                        except HTTPException as e:
                            st.error(e.detail)
