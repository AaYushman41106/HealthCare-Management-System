import pytest
from datetime import date, timedelta
from app.core.security import create_access_token, hash_password
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole


@pytest.fixture
def test_admin_user(db_session):
    admin = User(
        username="superadmin",
        email="superadmin@securecare.org",
        hashed_password=hash_password("SuperAdmin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_token(test_admin_user):
    return create_access_token(
        subject=test_admin_user.id,
        claims={"username": test_admin_user.username, "role": test_admin_user.role.value},
    )


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_patient_user(db_session):
    patient_user = User(
        username="patient_bob",
        email="bob@example.com",
        hashed_password=hash_password("BobSecure123!"),
        role=UserRole.PATIENT,
        is_active=True,
    )
    db_session.add(patient_user)
    db_session.commit()
    db_session.refresh(patient_user)

    patient_profile = Patient(user_id=patient_user.id, full_name="Bob Patient")
    db_session.add(patient_profile)
    db_session.commit()
    return patient_user


@pytest.fixture
def patient_token(test_patient_user):
    return create_access_token(
        subject=test_patient_user.id,
        claims={"username": test_patient_user.username, "role": test_patient_user.role.value},
    )


@pytest.fixture
def patient_headers(patient_token):
    return {"Authorization": f"Bearer {patient_token}"}


@pytest.fixture
def test_doctor_user(db_session):
    doc_user = User(
        username="dr_alice",
        email="alice@securecare.org",
        hashed_password=hash_password("DoctorSecure123!"),
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db_session.add(doc_user)
    db_session.commit()
    db_session.refresh(doc_user)

    doc_profile = Doctor(
        user_id=doc_user.id,
        full_name="Dr. Alice Smith",
        specialization="Neurology",
        license_number="LIC-NEURO-999",
        phone="+1-555-9999",
        is_active=True,
    )
    db_session.add(doc_profile)
    db_session.commit()
    return doc_user


@pytest.fixture
def doctor_token(test_doctor_user):
    return create_access_token(
        subject=test_doctor_user.id,
        claims={"username": test_doctor_user.username, "role": test_doctor_user.role.value},
    )


@pytest.fixture
def doctor_headers(doctor_token):
    return {"Authorization": f"Bearer {doctor_token}"}


# ========================================================
# ADMIN ACCESS CONTROL TESTS
# ========================================================

def test_admin_access_unauthenticated_rejected(client):
    """Admin endpoints must reject requests without valid credentials with 401."""
    res1 = client.get("/api/admin/users")
    assert res1.status_code == 401

    res2 = client.get("/api/admin/doctors")
    assert res2.status_code == 401

    res3 = client.get("/api/admin/audit-logs")
    assert res3.status_code == 401

    res4 = client.get("/api/admin/security-stats")
    assert res4.status_code == 401


def test_admin_access_forbidden_for_patient(client, patient_headers):
    """Patient role attempting to access admin endpoints must be rejected with 403."""
    res1 = client.get("/api/admin/users", headers=patient_headers)
    assert res1.status_code == 403

    res2 = client.get("/api/admin/doctors", headers=patient_headers)
    assert res2.status_code == 403

    res3 = client.get("/api/admin/audit-logs", headers=patient_headers)
    assert res3.status_code == 403

    res4 = client.get("/api/admin/security-stats", headers=patient_headers)
    assert res4.status_code == 403


def test_admin_access_forbidden_for_doctor(client, doctor_headers):
    """Doctor role attempting to access admin endpoints must be rejected with 403."""
    res1 = client.get("/api/admin/users", headers=doctor_headers)
    assert res1.status_code == 403

    res2 = client.get("/api/admin/doctors", headers=doctor_headers)
    assert res2.status_code == 403

    res3 = client.get("/api/admin/audit-logs", headers=doctor_headers)
    assert res3.status_code == 403

    res4 = client.get("/api/admin/security-stats", headers=doctor_headers)
    assert res4.status_code == 403


def test_admin_access_granted_for_admin(client, admin_headers):
    """Admin role is authorized to access all admin endpoints."""
    res_users = client.get("/api/admin/users", headers=admin_headers)
    assert res_users.status_code == 200

    res_doctors = client.get("/api/admin/doctors", headers=admin_headers)
    assert res_doctors.status_code == 200

    res_logs = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert res_logs.status_code == 200

    res_stats = client.get("/api/admin/security-stats", headers=admin_headers)
    assert res_stats.status_code == 200


# ========================================================
# USER MANAGEMENT & ACCOUNT STATUS TESTS
# ========================================================

def test_admin_list_users_and_filters(client, admin_headers, test_patient_user, test_doctor_user):
    """Admin can list users and filter by role or status."""
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3  # Admin, Patient, Doctor

    # Filter by PATIENT
    res_patient = client.get("/api/admin/users?role=PATIENT", headers=admin_headers)
    assert res_patient.status_code == 200
    for u in res_patient.json():
        assert u["role"] == "PATIENT"

    # Filter by DOCTOR
    res_doc = client.get("/api/admin/users?role=DOCTOR", headers=admin_headers)
    assert res_doc.status_code == 200
    for u in res_doc.json():
        assert u["role"] == "DOCTOR"


def test_admin_get_user_by_id(client, admin_headers, test_patient_user):
    """Admin can fetch a specific user profile and 404 on nonexistent ID."""
    res = client.get(f"/api/admin/users/{test_patient_user.id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["username"] == test_patient_user.username
    assert "hashed_password" not in res.json()

    res_nf = client.get("/api/admin/users/99999", headers=admin_headers)
    assert res_nf.status_code == 404


def test_admin_toggle_user_status_and_login_impact(client, admin_headers, test_patient_user):
    """Deactivating a user prevents login; re-activating restores access."""
    # Deactivate Bob
    res_deact = client.patch(
        f"/api/admin/users/{test_patient_user.id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # Attempt login while inactive
    res_login = client.post(
        "/api/auth/login",
        json={"username": "patient_bob", "password": "BobSecure123!"},
    )
    assert res_login.status_code == 400
    assert "inactive" in res_login.json()["detail"].lower()

    # Reactivate Bob
    res_react = client.patch(
        f"/api/admin/users/{test_patient_user.id}/status",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert res_react.status_code == 200
    assert res_react.json()["is_active"] is True

    # Bob can now log in successfully
    res_login_ok = client.post(
        "/api/auth/login",
        json={"username": "patient_bob", "password": "BobSecure123!"},
    )
    assert res_login_ok.status_code == 200
    assert "access_token" in res_login_ok.json()


def test_admin_cannot_deactivate_self(client, admin_headers, test_admin_user):
    """Admin is prevented from deactivating their own administrative account."""
    res = client.patch(
        f"/api/admin/users/{test_admin_user.id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert res.status_code == 400
    assert "cannot deactivate their own account" in res.json()["detail"]


# ========================================================
# DOCTOR MANAGEMENT TESTS
# ========================================================

def test_admin_list_and_get_doctors(client, admin_headers, test_doctor_user):
    """Admin can view detailed doctor list with account state."""
    res = client.get("/api/admin/doctors", headers=admin_headers)
    assert res.status_code == 200
    doctors = res.json()
    assert len(doctors) >= 1
    doc = doctors[0]
    assert doc["specialization"] == "Neurology"
    assert doc["user_email"] == "alice@securecare.org"
    assert doc["is_active"] is True

    # Get single doctor
    res_single = client.get(f"/api/admin/doctors/{doc['id']}", headers=admin_headers)
    assert res_single.status_code == 200
    assert res_single.json()["license_number"] == "LIC-NEURO-999"


def test_admin_deactivate_doctor_removes_from_scheduling(client, admin_headers, test_doctor_user, patient_headers):
    """Deactivating a doctor removes them from public availability and rejects bookings."""
    res_docs = client.get("/api/admin/doctors", headers=admin_headers)
    doctor_id = res_docs.json()[0]["id"]

    # Deactivate doctor
    res_deact = client.patch(
        f"/api/admin/doctors/{doctor_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # Check public doctors endpoint
    res_public = client.get("/api/doctors")
    assert res_public.status_code == 200
    available_doc_ids = [d["id"] for d in res_public.json()]
    assert doctor_id not in available_doc_ids

    # Patient attempt to book appointment with deactivated doctor fails with 404
    appt_date = (date.today() + timedelta(days=1)).isoformat()
    res_book = client.post(
        "/api/appointments",
        headers=patient_headers,
        json={
            "doctor_id": doctor_id,
            "appointment_date": appt_date,
            "appointment_time": "10:00",
            "reason": "General checkup",
        },
    )
    assert res_book.status_code == 404
    assert "doctor not found" in res_book.json()["detail"].lower()


# ========================================================
# AUDIT LOGS & SECURITY STATS TESTS
# ========================================================

def test_admin_audit_logs_and_self_logging(client, admin_headers):
    """Querying audit logs works, filters work, and viewing action is logged."""
    # Fetch logs
    res = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)

    # Next fetch will include the ADMIN_AUDIT_LOG_VIEWED event
    res_viewed = client.get("/api/admin/audit-logs?action=ADMIN_AUDIT_LOG_VIEWED", headers=admin_headers)
    assert res_viewed.status_code == 200
    view_logs = res_viewed.json()
    assert len(view_logs) >= 1
    assert view_logs[0]["action"] == "ADMIN_AUDIT_LOG_VIEWED"


def test_admin_security_stats_overview(client, admin_headers, test_patient_user, test_doctor_user):
    """Security statistics return expected totals and status distributions."""
    res = client.get("/api/admin/security-stats", headers=admin_headers)
    assert res.status_code == 200
    stats = res.json()

    assert stats["total_users"] >= 3
    assert stats["active_users"] >= 3
    assert stats["inactive_users"] >= 0
    assert stats["total_doctors"] >= 1
    assert stats["active_doctors"] >= 1
    assert "total_appointments" in stats
    assert "total_medical_records" in stats
    assert "total_audit_events" in stats
    assert "recent_failed_logins" in stats
    assert "security_alerts_count" in stats
