from datetime import date, timedelta
from app.core.security import hash_password
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.seed import seed_doctors


# Helper utilities for tests
def create_test_doctor(db_session, username="dr_smith", specialization="Cardiology"):
    """Helper to create an active doctor in the test database."""
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("DoctorPass123!"),
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    doctor = Doctor(
        user_id=user.id,
        full_name=f"Dr. {username.capitalize()}",
        specialization=specialization,
        license_number=f"LIC-{username.upper()}-99",
        phone="+1-555-1234",
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor, user


def login_user(client, username, password="Password123!"):
    """Helper to authenticate a user and return authorization bearer header."""
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_patient(client, username="patient_one"):
    """Helper to register a patient through public registration and login."""
    res = client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": "Password123!",
        "full_name": f"Test {username.capitalize()}",
    })
    assert res.status_code == 201
    headers = login_user(client, username, "Password123!")
    return headers, res.json()


# ---------------------------------------------------------
# Sprint 2 Automated Test Cases (18 Required Scenarios)
# ---------------------------------------------------------

def test_patient_can_create_appointment(client, db_session):
    """Test 1: Patient can create an appointment with valid doctor, date, time, reason."""
    doctor, _ = create_test_doctor(db_session, "dr_cardio")
    headers, patient_data = create_test_patient(client, "patient_alpha")

    appt_date = (date.today() + timedelta(days=2)).isoformat()
    payload = {
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "10:30",
        "reason": "Regular cardiology consultation",
    }

    res = client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 201

    data = res.json()
    assert data["doctor_id"] == doctor.id
    assert data["status"] == "PENDING"
    assert data["reason"] == "Regular cardiology consultation"
    assert data["appointment_time"] == "10:30"
    assert "id" in data


def test_patient_cannot_create_appointment_for_another_patient(client, db_session):
    """Test 2: Patient cannot spoof another patient's ID. Server strictly derives identity from token."""
    doctor, _ = create_test_doctor(db_session, "dr_general")
    headers_a, patient_a = create_test_patient(client, "patient_a")
    _, patient_b = create_test_patient(client, "patient_b")

    appt_date = (date.today() + timedelta(days=3)).isoformat()
    # Attacker tries to inject client-side patient_id of patient B
    payload = {
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "14:00",
        "reason": "Spoofed appointment attempt",
        "patient_id": patient_b["id"],
    }

    res = client.post("/api/appointments", json=payload, headers=headers_a)
    assert res.status_code == 201
    data = res.json()

    # The appointment MUST be linked to Patient A's profile, NOT Patient B's profile
    user_a = db_session.query(User).filter(User.username == "patient_a").first()
    assert data["patient_id"] == user_a.patient_profile.id
    user_b = db_session.query(User).filter(User.username == "patient_b").first()
    assert data["patient_id"] != user_b.patient_profile.id


def test_patient_can_view_own_appointments(client, db_session):
    """Test 3: Patient can view their own appointments list."""
    doctor, _ = create_test_doctor(db_session, "dr_p3")
    headers, _ = create_test_patient(client, "patient_p3")

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "11:00",
        "reason": "General checkup",
    }, headers=headers)

    res = client.get("/api/appointments", headers=headers)
    assert res.status_code == 200
    appts = res.json()
    assert len(appts) == 1
    assert appts[0]["reason"] == "General checkup"


def test_patient_cannot_view_another_patient_appointment(client, db_session):
    """Test 4: Patient cannot access another patient's appointment details (403 Forbidden)."""
    doctor, _ = create_test_doctor(db_session, "dr_p4")
    headers_a, _ = create_test_patient(client, "patient_4a")
    headers_b, _ = create_test_patient(client, "patient_4b")

    # Patient A creates appointment
    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "15:00",
        "reason": "Private diagnosis",
    }, headers=headers_a)
    appt_id = res_create.json()["id"]

    # Patient B attempts to access Patient A's appointment
    res_access = client.get(f"/api/appointments/{appt_id}", headers=headers_b)
    assert res_access.status_code in (403, 404)
    if res_access.status_code == 403:
        assert "another patient" in res_access.json()["detail"].lower()


def test_doctor_can_view_their_appointments(client, db_session):
    """Test 5: Doctor can view appointments assigned to them."""
    doctor, _ = create_test_doctor(db_session, "dr_p5")
    doc_headers = login_user(client, "dr_p5", "DoctorPass123!")

    headers_pat, _ = create_test_patient(client, "patient_p5")
    appt_date = (date.today() + timedelta(days=2)).isoformat()
    client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "09:30",
        "reason": "Cardiology screening",
    }, headers=headers_pat)

    res = client.get("/api/appointments", headers=doc_headers)
    assert res.status_code == 200
    doc_appts = res.json()
    assert len(doc_appts) == 1
    assert doc_appts[0]["doctor_id"] == doctor.id


def test_doctor_cannot_view_another_doctor_appointment(client, db_session):
    """Test 6: Doctor cannot access appointments scheduled with another doctor."""
    doctor_1, _ = create_test_doctor(db_session, "dr_doc1")
    doctor_2, _ = create_test_doctor(db_session, "dr_doc2")

    doc1_headers = login_user(client, "dr_doc1", "DoctorPass123!")
    doc2_headers = login_user(client, "dr_doc2", "DoctorPass123!")

    headers_pat, _ = create_test_patient(client, "patient_p6")
    appt_date = (date.today() + timedelta(days=2)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor_1.id,
        "appointment_date": appt_date,
        "appointment_time": "10:00",
        "reason": "Doc1 exclusive appt",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    # Doctor 2 attempts to view Doctor 1's appointment
    res = client.get(f"/api/appointments/{appt_id}", headers=doc2_headers)
    assert res.status_code in (403, 404)


def test_doctor_can_confirm_own_appointment(client, db_session):
    """Test 7: Doctor can confirm a PENDING appointment assigned to them."""
    doctor, _ = create_test_doctor(db_session, "dr_confirm")
    doc_headers = login_user(client, "dr_confirm", "DoctorPass123!")

    headers_pat, _ = create_test_patient(client, "patient_p7")
    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "11:30",
        "reason": "Follow up consultation",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    res_patch = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "CONFIRMED", "notes": "Approved by Dr. Confirm"},
        headers=doc_headers,
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "CONFIRMED"
    assert "Approved" in res_patch.json()["notes"]


def test_doctor_can_reject_own_appointment(client, db_session):
    """Test 8: Doctor can reject a PENDING appointment assigned to them."""
    doctor, _ = create_test_doctor(db_session, "dr_reject")
    doc_headers = login_user(client, "dr_reject", "DoctorPass123!")

    headers_pat, _ = create_test_patient(client, "patient_p8")
    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "12:00",
        "reason": "Conflict consultation",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    res_patch = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "REJECTED", "notes": "Doctor unavailable at requested slot."},
        headers=doc_headers,
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "REJECTED"


def test_doctor_can_complete_confirmed_appointment(client, db_session):
    """Test 9: Doctor can transition CONFIRMED appointment to COMPLETED."""
    doctor, _ = create_test_doctor(db_session, "dr_complete")
    doc_headers = login_user(client, "dr_complete", "DoctorPass123!")

    headers_pat, _ = create_test_patient(client, "patient_p9")
    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "13:00",
        "reason": "Routine check",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    # First confirm
    client.patch(f"/api/appointments/{appt_id}", json={"status": "CONFIRMED"}, headers=doc_headers)

    # Then complete
    res_complete = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "COMPLETED", "notes": "Patient examined. Medication prescribed."},
        headers=doc_headers,
    )
    assert res_complete.status_code == 200
    assert res_complete.json()["status"] == "COMPLETED"


def test_patient_can_cancel_own_pending_appointment(client, db_session):
    """Test 10: Patient can cancel their own pending appointment via DELETE or PATCH."""
    doctor, _ = create_test_doctor(db_session, "dr_cancel")
    headers_pat, _ = create_test_patient(client, "patient_p10")

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "14:00",
        "reason": "Cancel test",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    # Cancel via DELETE endpoint (soft cancel)
    res_del = client.delete(f"/api/appointments/{appt_id}", headers=headers_pat)
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "CANCELLED"

    # Verify status in database
    db_appt = db_session.query(Appointment).filter(Appointment.id == appt_id).first()
    assert db_appt is not None
    assert db_appt.status == AppointmentStatus.CANCELLED


def test_patient_cannot_confirm_appointment(client, db_session):
    """Test 11: Patient cannot modify appointment status to CONFIRMED (403 Forbidden)."""
    doctor, _ = create_test_doctor(db_session, "dr_unauth1")
    headers_pat, _ = create_test_patient(client, "patient_p11")

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "15:00",
        "reason": "Status privilege escalation test",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    res_patch = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "CONFIRMED"},
        headers=headers_pat,
    )
    assert res_patch.status_code == 403
    assert "not permitted" in res_patch.json()["detail"].lower()


def test_patient_cannot_complete_appointment(client, db_session):
    """Test 12: Patient cannot modify appointment status to COMPLETED (403 Forbidden)."""
    doctor, _ = create_test_doctor(db_session, "dr_unauth2")
    headers_pat, _ = create_test_patient(client, "patient_p12")

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "16:00",
        "reason": "Complete privilege escalation test",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    res_patch = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "COMPLETED"},
        headers=headers_pat,
    )
    assert res_patch.status_code == 403


def test_doctor_cannot_modify_another_doctor_appointment(client, db_session):
    """Test 13: Doctor cannot modify an appointment belonging to another doctor (403 Forbidden)."""
    doc_1, _ = create_test_doctor(db_session, "dr_doc1_mod")
    doc_2, _ = create_test_doctor(db_session, "dr_doc2_mod")

    doc2_headers = login_user(client, "dr_doc2_mod", "DoctorPass123!")
    headers_pat, _ = create_test_patient(client, "patient_p13")

    appt_date = (date.today() + timedelta(days=2)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doc_1.id,
        "appointment_date": appt_date,
        "appointment_time": "10:00",
        "reason": "Dr 1 appointment",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    # Doctor 2 attempts to confirm Doctor 1's appointment
    res = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "CONFIRMED"},
        headers=doc2_headers,
    )
    assert res.status_code in (403, 404)


def test_unauthenticated_user_cannot_access_appointment_apis(client):
    """Test 14: Unauthenticated requests without JWT tokens are rejected (401 Unauthorized)."""
    res_list = client.get("/api/appointments")
    assert res_list.status_code == 401

    res_create = client.post("/api/appointments", json={
        "doctor_id": 1,
        "appointment_date": str(date.today()),
        "appointment_time": "10:00",
        "reason": "No auth check",
    })
    assert res_create.status_code == 401

    res_get = client.get("/api/appointments/1")
    assert res_get.status_code == 401

    res_patch = client.patch("/api/appointments/1", json={"status": "CANCELLED"})
    assert res_patch.status_code == 401


def test_invalid_doctor_id_is_rejected(client, db_session):
    """Test 15: Booking an appointment with non-existent doctor ID returns 404."""
    headers_pat, _ = create_test_patient(client, "patient_p15")

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res = client.post("/api/appointments", json={
        "doctor_id": 99999,
        "appointment_date": appt_date,
        "appointment_time": "10:00",
        "reason": "Non-existent doctor appointment",
    }, headers=headers_pat)
    assert res.status_code == 404
    assert "doctor not found" in res.json()["detail"].lower()


def test_invalid_appointment_id_handled_correctly(client, db_session):
    """Test 16: Operations on non-existent appointment ID return 404 Not Found."""
    headers_pat, _ = create_test_patient(client, "patient_p16")

    res_get = client.get("/api/appointments/99999", headers=headers_pat)
    assert res_get.status_code == 404

    res_patch = client.patch("/api/appointments/99999", json={"status": "CANCELLED"}, headers=headers_pat)
    assert res_patch.status_code == 404

    res_del = client.delete("/api/appointments/99999", headers=headers_pat)
    assert res_del.status_code == 404


def test_invalid_status_transition_is_rejected(client, db_session):
    """Test 17: Illegal state transitions are rejected with 400 Bad Request."""
    doctor, _ = create_test_doctor(db_session, "dr_transition")
    doc_headers = login_user(client, "dr_transition", "DoctorPass123!")
    headers_pat, _ = create_test_patient(client, "patient_p17")

    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_create = client.post("/api/appointments", json={
        "doctor_id": doctor.id,
        "appointment_date": appt_date,
        "appointment_time": "11:00",
        "reason": "Transition rules test",
    }, headers=headers_pat)
    appt_id = res_create.json()["id"]

    # 1. PENDING -> COMPLETED directly is illegal
    res_bad_comp = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "COMPLETED"},
        headers=doc_headers,
    )
    assert res_bad_comp.status_code == 400
    assert "must be confirmed before" in res_bad_comp.json()["detail"].lower()

    # Confirm appointment legally
    client.patch(f"/api/appointments/{appt_id}", json={"status": "CONFIRMED"}, headers=doc_headers)

    # Complete appointment legally
    client.patch(f"/api/appointments/{appt_id}", json={"status": "COMPLETED"}, headers=doc_headers)

    # 2. COMPLETED -> PENDING is illegal
    res_bad_revert = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "PENDING"},
        headers=doc_headers,
    )
    assert res_bad_revert.status_code == 400

    # 3. COMPLETED -> CONFIRMED is illegal (terminal status)
    res_bad_mod = client.patch(
        f"/api/appointments/{appt_id}",
        json={"status": "CONFIRMED"},
        headers=doc_headers,
    )
    assert res_bad_mod.status_code == 400
    assert "terminal status" in res_bad_mod.json()["detail"].lower()


def test_seed_operation_is_idempotent(db_session):
    """Test 18: Doctor seed operation is idempotent and creates exactly two development doctors."""
    # First seed run
    count1 = seed_doctors(db=db_session)
    assert count1 == 2

    # Second seed run (must not create duplicates)
    count2 = seed_doctors(db=db_session)
    assert count2 == 0

    doctors = db_session.query(Doctor).all()
    # Exactly 2 development doctors are present
    usernames = [d.user.username for d in doctors]
    assert "dr_priya" in usernames
    assert "dr_rahul" in usernames
    assert len(doctors) == 2
