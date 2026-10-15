"""Electronic Medical Records (EMR) — Clinical Records Presentation & Authoring."""
import streamlit as st
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.schemas.medical_record import MedicalRecordCreateRequest
from app.services.medical_record_service import create_medical_record, get_medical_records
from app.ui.components import empty_state, section_heading


def render_medical_records_list(db: Session, current_user: User) -> None:
    """Render authorized electronic medical records with clear diagnostic cards."""
    records = get_medical_records(db, current_user)
    if not records:
        empty_state("No Medical Records on File", "There are currently no authorized clinical diagnoses or prescriptions recorded.")
        return

    section_heading(f"Authorized Clinical Records ({len(records)})", "Detailed consultation findings, diagnoses, and authorized prescriptions.")

    for rec in records:
        with st.container(border=True):
            col_diag, col_meta = st.columns([3, 2])
            with col_diag:
                st.markdown(f"### 📋 {rec.diagnosis}")
                st.caption(f"Medical Record #{rec.id} | Associated Consultation #{rec.appointment_id}")
            with col_meta:
                date_str = rec.created_at.strftime("%B %d, %Y") if rec.created_at else "Recent"
                doc_name = f"Dr. {rec.doctor.full_name}" if rec.doctor else f"Physician #{rec.doctor_id}"
                st.markdown(f"**Attending Physician:** {doc_name}")
                st.caption(f"Authorized on: {date_str}")

            st.divider()

            col_sym, col_rx = st.columns(2)
            with col_sym:
                st.markdown("**Reported Symptoms & Onset:**")
                st.write(rec.symptoms or "None noted.")

                st.markdown("**Clinical Treatment Plan:**")
                st.write(rec.treatment or "Routine monitoring advised.")

            with col_rx:
                st.markdown("**Prescribed Medication & Regimen:**")
                st.info(rec.prescription or "No active pharmacological prescription.")

                if rec.notes:
                    st.markdown("**Physician Clinical Notes:**")
                    st.caption(rec.notes)


def render_record_authoring_form(db: Session, current_user: User) -> None:
    """Render structured EMR authoring form for completed consultations."""
    if current_user.role != UserRole.DOCTOR or not current_user.doctor_profile:
        st.error("Access Forbidden: Only credentialed medical doctors may author clinical records.")
        return

    doc_id = current_user.doctor_profile.id
    completed_appts = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doc_id,
            Appointment.status == AppointmentStatus.COMPLETED,
        )
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    eligible_appts = [a for a in completed_appts if not a.medical_record]
    if not eligible_appts:
        empty_state(
            "No Consultations Pending Documentation",
            "All completed patient visits have been fully documented, or no visits are currently marked COMPLETED.",
        )
        return

    section_heading("Document Consultation & Issue Prescriptions", "Author an official diagnosis, treatment plan, and prescription for a completed visit.")

    options = {
        f"Visit #{a.id} — {a.patient.full_name if a.patient else a.patient_id} ({a.appointment_date} @ {a.appointment_time})": a.id
        for a in eligible_appts
    }

    with st.container(border=True):
        with st.form("author_emr_form"):
            selected_label = st.selectbox("Select Completed Consultation *", options=list(options.keys()))
            selected_appt_id = options[selected_label]

            col_d, col_s = st.columns(2)
            with col_d:
                diagnosis = st.text_input("Official Clinical Diagnosis *", placeholder="e.g. Acute Bronchitis")
            with col_s:
                symptoms = st.text_input("Observed Symptoms & Vitals *", placeholder="e.g. Productive cough, low-grade fever")

            treatment = st.text_area("Treatment Plan & Care Instructions *", placeholder="e.g. Oral hydration, bed rest for 48 hours")
            prescription = st.text_area("Pharmacological Prescription (Rx) *", placeholder="e.g. Azithromycin 250mg qd x 5 days, Guaifenesin 400mg q6h prn")
            notes = st.text_area("Physician Notes (Optional)", placeholder="Patient advised to follow up if respiratory symptoms worsen")

            st.caption("🔒 Once submitted, this clinical record is permanently attached to the consultation and recorded in the audit log.")
            submit_btn = st.form_submit_button("Sign & Authorize Clinical Record", type="primary", use_container_width=True)

        if submit_btn:
            if not diagnosis or not symptoms or not treatment or not prescription:
                st.warning("All mandatory clinical fields (Diagnosis, Symptoms, Treatment, Prescription) must be completed.")
            else:
                try:
                    payload = MedicalRecordCreateRequest(
                        appointment_id=selected_appt_id,
                        diagnosis=diagnosis.strip(),
                        symptoms=symptoms.strip(),
                        treatment=treatment.strip(),
                        prescription=prescription.strip(),
                        notes=notes.strip() if notes else None,
                    )
                    rec = create_medical_record(db=db, current_user=current_user, payload=payload)
                    st.success(f"Clinical Record #{rec.id} successfully authorized for Patient #{rec.patient_id}!")
                    st.rerun()
                except HTTPException as e:
                    st.error(f"Validation Failure: {e.detail}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")
