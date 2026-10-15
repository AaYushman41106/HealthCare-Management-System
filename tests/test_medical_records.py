from datetime import date, timedelta
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User, UserRole
from tests.test_appointments import create_test_doctor, create_test_patient, login_user


def setup_completed_appointment(client, db_session, doc_username="dr_rec_doc", pat_username="pat_rec_pat"):
    """Helper creating an authenticated doctor, patient, and a COMPLETED appointment."""
    doctor, doc_user = create_test_doctor(db_session, doc_username, "Internal Medicine")
    doc_headers = login_user(client, doc_username, "DoctorPass123!")

    pat_headers, pat_data = create_test_patient(client, pat_username)

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_book = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "10:00",
        "reason": "Consultation for clinical diagnosis",
    }, headers=pat_headers)
    assert res_book.status_code == 201
    appt_id = res_book.json()["id"]

    # Confirm appointment
    client.patch(f"/api/appointments/{appt_id}", json={"status": "CONFIRMED"}, headers=doc_headers)

    # Complete appointment
    res_comp = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "COMPLETED", "notes": "Consultation concluded."},
        headers=doc_headers,
    )
    assert res_comp.status_code == 200

    return doctor, doc_headers, pat_headers, appt_id


# -------------------------------------------------------------
# Sprint 3 Automated Tests (20 Scenarios)
# -------------------------------------------------------------

def test_doctor_can_create_medical_record_for_completed_appointment(client, db_session):
    """Test 1: Doctor can create medical record for an eligible COMPLETED consultation."""
    doctor, doc_headers, _, appt_id = setup_completed_appointment(client, db_session, "dr_med1", "pat_med1")

    payload = {
        "appointment_id": appt_id,
        "diagnosis": "Acute Bronchitis",
        "symptoms": "Persistent cough, mild fever, fatigue",
        "treatment": "Rest, hydration, inhaler therapy",
        "prescription": "Albuterol Inhaler 90mcg, Amoxicillin 500mg TID 7 days",
        "notes": "Patient advised to follow up if fever persists beyond 3 days.",
    }

    res = client.post("/api/medical-records", json=payload, headers=doc_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["appointment_id"] == appt_id
    assert data["doctor_id"] == doctor.id
    assert data["diagnosis"] == "Acute Bronchitis"
    assert "Albuterol" in data["prescription"]
    assert "id" in data


def test_patient_cannot_create_medical_record(client, db_session):
    """Test 2: Patient cannot create a medical record (403 Forbidden)."""
    _, _, pat_headers, appt_id = setup_completed_appointment(client, db_session, "dr_med2", "pat_med2")

    payload = {
        "appointment_id": appt_id,
        "diagnosis": "Self-diagnosed Flu",
        "symptoms": "Cough",
        "treatment": "Rest",
    }
    res = client.post("/api/medical-records", json=payload, headers=pat_headers)
    assert res.status_code == 403
    assert "only doctors" in res.json()["detail"].lower()


def test_doctor_cannot_create_record_for_another_doctor_appointment(client, db_session):
    """Test 3: Doctor cannot create medical record for an appointment belonging to another doctor."""
    doctor_1, _, _, appt_id = setup_completed_appointment(client, db_session, "dr_med3a", "pat_med3")

    # Second doctor
    doctor_2, _ = create_test_doctor(db_session, "dr_med3b", "Pediatrics")
    doc2_headers = login_user(client, "dr_med3b", "DoctorPass123!")

    payload = {
        "appointment_id": appt_id,
        "diagnosis": "Intruder diagnosis",
        "symptoms": "N/A",
        "treatment": "N/A",
    }
    res = client.post("/api/medical-records", json=payload, headers=doc2_headers)
    assert res.status_code == 403
    assert "another doctor" in res.json()["detail"].lower()


def test_doctor_cannot_create_record_for_incomplete_appointment(client, db_session):
    """Test 4: Doctor cannot create medical record for an appointment that is not yet COMPLETED."""
    doctor, _ = create_test_doctor(db_session, "dr_med4", "Cardiology")
    doc_headers = login_user(client, "dr_med4", "DoctorPass123!")
    pat_headers, _ = create_test_patient(client, "pat_med4")

    # Create PENDING appointment
    appt_date = (date.today() + timedelta(days=2)).isoformat()
    res_book = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "11:00",
        "reason": "Preliminary checkup",
    }, headers=pat_headers)
    appt_id = res_book.json()["id"]

    # Attempt to create medical record while PENDING
    payload = {
        "appointment_id": appt_id,
        "diagnosis": "Premature record",
        "symptoms": "N/A",
        "treatment": "N/A",
    }
    res_pending = client.post("/api/medical-records", json=payload, headers=doc_headers)
    assert res_pending.status_code == 400
    assert "completed" in res_pending.json()["detail"].lower()

    # Confirm appointment (CONFIRMED status)
    client.patch(f"/api/appointments/{appt_id}", json={"status": "CONFIRMED"}, headers=doc_headers)

    # Attempt to create medical record while CONFIRMED
    res_confirmed = client.post("/api/medical-records", json=payload, headers=doc_headers)
    assert res_confirmed.status_code == 400
    assert "completed" in res_confirmed.json()["detail"].lower()


def test_duplicate_medical_record_rejected(client, db_session):
    """Test 5: Duplicate medical record for the same appointment is rejected."""
    _, doc_headers, _, appt_id = setup_completed_appointment(client, db_session, "dr_med5", "pat_med5")

    payload = {
        "appointment_id": appt_id,
        "diagnosis": "Initial diagnosis",
        "symptoms": "Fever",
        "treatment": "Paracetamol",
    }
    res1 = client.post("/api/medical-records", json=payload, headers=doc_headers)
    assert res1.status_code == 201

    # Attempt duplicate
    res2 = client.post("/api/medical-records", json=payload, headers=doc_headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_patient_can_view_own_medical_records(client, db_session):
    """Test 6: Patient can view their own medical records."""
    _, doc_headers, pat_headers, appt_id = setup_completed_appointment(client, db_session, "dr_med6", "pat_med6")

    client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Hypertension Stage 1",
        "symptoms": "Elevated blood pressure reading",
        "treatment": "Dietary sodium reduction and lifestyle changes",
        "prescription": "Amlodipine 5mg OD",
    }, headers=doc_headers)

    res = client.get("/api/medical-records", headers=pat_headers)
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 1
    assert records[0]["diagnosis"] == "Hypertension Stage 1"


def test_patient_cannot_view_another_patient_medical_record(client, db_session):
    """Test 7: Patient cannot access another patient's medical record (403 Forbidden)."""
    _, doc_headers, _, appt_id = setup_completed_appointment(client, db_session, "dr_med7", "pat_med7a")
    headers_b, _ = create_test_patient(client, "pat_med7b")

    res_create = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Confidential diagnosis Patient A",
        "symptoms": "Confidential",
        "treatment": "Confidential",
    }, headers=doc_headers)
    record_id = res_create.json()["id"]

    # Patient B attempts to access Patient A's record
    res_access = client.get(f"/api/medical-records/{record_id}", headers=headers_b)
    assert res_access.status_code == 403
    assert "another patient" in res_access.json()["detail"].lower()


def test_unauthorized_doctor_cannot_view_another_doctor_record(client, db_session):
    """Test 8: Doctor cannot access medical records created by another doctor (403 Forbidden)."""
    _, doc1_headers, _, appt_id = setup_completed_appointment(client, db_session, "dr_med8a", "pat_med8")

    # Create doctor 2
    create_test_doctor(db_session, "dr_med8b", "Neurology")
    doc2_headers = login_user(client, "dr_med8b", "DoctorPass123!")

    res_create = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Doctor 1 clinical record",
        "symptoms": "Symptoms",
        "treatment": "Treatment",
    }, headers=doc1_headers)
    record_id = res_create.json()["id"]

    # Doctor 2 attempts access
    res = client.get(f"/api/medical-records/{record_id}", headers=doc2_headers)
    assert res.status_code == 403
    assert "another doctor" in res.json()["detail"].lower()


def test_medical_record_response_does_not_expose_password_hashes(client, db_session):
    """Test 9: Medical record response never exposes password hashes."""
    _, doc_headers, pat_headers, appt_id = setup_completed_appointment(client, db_session, "dr_med9", "pat_med9")

    res_create = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Exposure test",
        "symptoms": "None",
        "treatment": "None",
    }, headers=doc_headers)
    record_id = res_create.json()["id"]

    res_get = client.get(f"/api/medical-records/{record_id}", headers=pat_headers)
    data = res_get.json()
    raw_str = res_get.text

    assert "password" not in data
    assert "hashed_password" not in data
    assert "$2b$" not in raw_str


def test_medical_record_response_does_not_expose_jwt_tokens(client, db_session):
    """Test 10: Medical record response never exposes JWT or authorization token data."""
    _, doc_headers, pat_headers, appt_id = setup_completed_appointment(client, db_session, "dr_med10", "pat_med10")

    res_create = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Token test",
        "symptoms": "None",
        "treatment": "None",
    }, headers=doc_headers)
    record_id = res_create.json()["id"]

    res_get = client.get(f"/api/medical-records/{record_id}", headers=pat_headers)
    data = res_get.json()

    assert "access_token" not in data
    assert "token_type" not in data


def test_audit_event_generated_on_record_creation(client, db_session):
    """Test 11: Audit log entry created with action MEDICAL_RECORD_CREATED."""
    _, doc_headers, _, appt_id = setup_completed_appointment(client, db_session, "dr_med11", "pat_med11")

    res = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Audit creation test",
        "symptoms": "Fever",
        "treatment": "Rest",
    }, headers=doc_headers)
    record_id = res.json()["id"]

    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == "MEDICAL_RECORD_CREATED",
        AuditLog.resource_id == str(record_id),
    ).first()
    assert audit_entry is not None
    assert audit_entry.resource_type == "medical_record"
    assert audit_entry.timestamp is not None


def test_audit_event_generated_on_record_viewing(client, db_session):
    """Test 12: Audit log entry created with action MEDICAL_RECORD_VIEWED."""
    _, doc_headers, pat_headers, appt_id = setup_completed_appointment(client, db_session, "dr_med12", "pat_med12")

    res_create = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Audit view test",
        "symptoms": "Headache",
        "treatment": "Hydration",
    }, headers=doc_headers)
    record_id = res_create.json()["id"]

    # View record
    client.get(f"/api/medical-records/{record_id}", headers=pat_headers)

    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == "MEDICAL_RECORD_VIEWED",
        AuditLog.resource_id == str(record_id),
    ).first()
    assert audit_entry is not None


def test_audit_event_generated_on_denied_record_access(client, db_session):
    """Test 13: Audit log entry created with action MEDICAL_RECORD_ACCESS_DENIED on unauthorized access."""
    _, doc_headers, _, appt_id = setup_completed_appointment(client, db_session, "dr_med13", "pat_med13a")
    headers_intruder, _ = create_test_patient(client, "pat_med13b")

    res_create = client.post("/api/medical-records", json={
        "appointment_id": appt_id,
        "diagnosis": "Restricted file",
        "symptoms": "Private",
        "treatment": "Private",
    }, headers=doc_headers)
    record_id = res_create.json()["id"]

    # Intruder access
    client.get(f"/api/medical-records/{record_id}", headers=headers_intruder)

    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.action == "MEDICAL_RECORD_ACCESS_DENIED",
        AuditLog.resource_id == str(record_id),
    ).first()
    assert audit_entry is not None


def test_audit_event_generated_on_successful_login(client, db_session):
    """Test 14: Audit log entry created on successful user login."""
    create_test_patient(client, "audit_login_user")

    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "LOGIN_SUCCESS",
    ).first()
    assert audit is not None
    assert audit.resource_type == "auth"


def test_audit_event_generated_on_failed_login(client, db_session):
    """Test 15: Audit log entry created on failed login attempt."""
    client.post("/api/auth/login", json={
        "username": "non_existent_account_audit",
        "password": "WrongPassword123!",
    })

    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "LOGIN_FAILURE",
        AuditLog.details.like("%non_existent_account_audit%"),
    ).first()
    assert audit is not None


def test_audit_event_generated_on_appointment_creation(client, db_session):
    """Test 16: Audit log entry created on appointment creation."""
    doctor, _ = create_test_doctor(db_session, "dr_audit_appt")
    pat_headers, _ = create_test_patient(client, "pat_audit_appt")

    appt_date = (date.today() + timedelta(days=3)).isoformat()
    res = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "14:30",
        "reason": "Audit verification appointment",
    }, headers=pat_headers)
    appt_id = res.json()["id"]

    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "APPOINTMENT_CREATED",
        AuditLog.resource_id == str(appt_id),
    ).first()
    assert audit is not None


def test_audit_event_generated_on_appointment_status_update(client, db_session):
    """Test 17: Audit log entry created on appointment status changes."""
    doctor, _ = create_test_doctor(db_session, "dr_audit_upd")
    doc_headers = login_user(client, "dr_audit_upd", "DoctorPass123!")
    pat_headers, _ = create_test_patient(client, "pat_audit_upd")

    appt_date = (date.today() + timedelta(days=2)).isoformat()
    res = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "15:00",
        "reason": "Audit update appointment",
    }, headers=pat_headers)
    appt_id = res.json()["id"]

    # Confirm appointment
    client.patch(f"/api/appointments/{appt_id}", json={"status": "CONFIRMED"}, headers=doc_headers)

    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "APPOINTMENT_UPDATED",
        AuditLog.resource_id == str(appt_id),
    ).first()
    assert audit is not None


def test_doctor_cannot_double_book_same_time_slot(client, db_session):
    """Test 18: Doctor collision prevention rejects double-booking the same date and time slot."""
    doctor, _ = create_test_doctor(db_session, "dr_collision1")
    pat1_headers, _ = create_test_patient(client, "pat_col1a")
    pat2_headers, _ = create_test_patient(client, "pat_col1b")

    shared_date = (date.today() + timedelta(days=3)).isoformat()
    shared_time = "10:30"

    # Patient 1 books the slot
    res1 = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": shared_date,
        "appointment_time": shared_time,
        "reason": "First booking",
    }, headers=pat1_headers)
    assert res1.status_code == 201

    # Patient 2 attempts to book the EXACT SAME doctor, date, and time
    res2 = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": shared_date,
        "appointment_time": shared_time,
        "reason": "Conflicting second booking",
    }, headers=pat2_headers)

    assert res2.status_code in (400, 409)
    assert "already booked" in res2.json()["detail"].lower()


def test_cancelled_appointment_allows_slot_reuse(client, db_session):
    """Test 19: A cancelled appointment frees the time slot for new bookings."""
    doctor, _ = create_test_doctor(db_session, "dr_collision2")
    pat1_headers, _ = create_test_patient(client, "pat_col2a")
    pat2_headers, _ = create_test_patient(client, "pat_col2b")

    shared_date = (date.today() + timedelta(days=4)).isoformat()
    shared_time = "11:00"

    # Patient 1 books
    res1 = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": shared_date,
        "appointment_time": shared_time,
        "reason": "First booking to be cancelled",
    }, headers=pat1_headers)
    appt_id = res1.json()["id"]

    # Patient 1 cancels
    client.delete(f"/api/appointments/{appt_id}", headers=pat1_headers)

    # Patient 2 books the exact same date and time - should SUCCEED now
    res2 = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": shared_date,
        "appointment_time": shared_time,
        "reason": "Re-booked slot after cancellation",
    }, headers=pat2_headers)

    assert res2.status_code == 201
    assert res2.json()["appointment_time"] == shared_time


def test_rejected_appointment_allows_slot_reuse(client, db_session):
    """Test 20: A rejected appointment frees the time slot for new bookings."""
    doctor, _ = create_test_doctor(db_session, "dr_collision3")
    doc_headers = login_user(client, "dr_collision3", "DoctorPass123!")
    pat1_headers, _ = create_test_patient(client, "pat_col3a")
    pat2_headers, _ = create_test_patient(client, "pat_col3b")

    shared_date = (date.today() + timedelta(days=5)).isoformat()
    shared_time = "14:00"

    # Patient 1 books
    res1 = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": shared_date,
        "appointment_time": shared_time,
        "reason": "Booking to be rejected",
    }, headers=pat1_headers)
    appt_id = res1.json()["id"]

    # Doctor rejects appointment
    client.patch(f"/api/appointments/{appt_id}", json={"status": "REJECTED"}, headers=doc_headers)

    # Patient 2 books the exact same date and time - should SUCCEED
    res2 = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": shared_date,
        "appointment_time": shared_time,
        "reason": "Re-booked slot after rejection",
    }, headers=pat2_headers)

    assert res2.status_code == 201
    assert res2.json()["appointment_time"] == shared_time
