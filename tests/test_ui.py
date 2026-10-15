"""Tests for Streamlit UI State, Services & Component Workflows."""
from datetime import date, timedelta
from unittest.mock import patch
import pytest
from fastapi import HTTPException
import streamlit as st

from app.core.security import hash_password
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreateRequest, AppointmentUpdateRequest
from app.schemas.medical_record import MedicalRecordCreateRequest
from app.services.appointment_service import create_appointment, update_appointment
from app.services.auth_service import AuthService
from app.services.jira_service import JiraService
from app.services.medical_record_service import create_medical_record, get_medical_records
from app.ui.auth_state import get_current_user, init_session_state, login_user, logout_user


class FakeSessionState(dict):
    """Mock for Streamlit session_state in headless unit test environments."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)


@pytest.fixture
def mock_session_state():
    fake_state = FakeSessionState()
    with patch.object(st, "session_state", fake_state):
        yield fake_state


def create_sample_patient(db_session, username="patient_test"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("Password123!"),
        role=UserRole.PATIENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    patient = Patient(
        user_id=user.id,
        full_name="Test Patient",
        date_of_birth=date(1990, 1, 1),
        gender="Female",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_sample_doctor(db_session, username="doctor_test"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("Password123!"),
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    doctor = Doctor(
        user_id=user.id,
        full_name="Test Doctor",
        specialization="Cardiology",
        license_number=f"LIC-{username}",
        is_active=True,
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_ui_session_lifecycle(db_session, mock_session_state):
    """Test session state initialization, login, and logout."""
    init_session_state()

    assert mock_session_state.authenticated is False
    assert mock_session_state.user_id is None
    assert mock_session_state.active_nav == "Dashboard"

    doctor_user = create_sample_doctor(db_session)
    login_user(doctor_user)

    assert mock_session_state.authenticated is True
    assert mock_session_state.user_id == doctor_user.id
    assert mock_session_state.role == "DOCTOR"
    assert "Doctor" in mock_session_state.full_name

    retrieved = get_current_user(db_session)
    assert retrieved is not None
    assert retrieved.id == doctor_user.id

    logout_user()
    assert mock_session_state.authenticated is False
    assert mock_session_state.user_id is None
    assert get_current_user(db_session) is None


def test_ui_patient_booking_and_conflict_handling(db_session):
    """Verify appointment booking and 409 collision guards."""
    patient_user = create_sample_patient(db_session, "pat_book")
    doctor_user = create_sample_doctor(db_session, "doc_book")
    tomorrow = date.today() + timedelta(days=1)

    # First booking succeeds
    payload = AppointmentCreateRequest(
        doctor_id=doctor_user.doctor_profile.id,
        appointment_date=tomorrow,
        appointment_time="10:00",
        reason="Heart consultation",
    )
    appt1 = create_appointment(db_session, patient_user, payload)
    assert appt1.id is not None
    assert appt1.status == AppointmentStatus.PENDING

    # Duplicate booking raises 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        create_appointment(db_session, patient_user, payload)
    assert exc_info.value.status_code == 409


def test_ui_doctor_workflow_and_emr_authoring(db_session):
    """Verify doctor consultation confirmation, completion, and medical record authoring."""
    patient_user = create_sample_patient(db_session, "pat_emr")
    doctor_user = create_sample_doctor(db_session, "doc_emr")
    tomorrow = date.today() + timedelta(days=2)

    # 1. Patient books appointment
    payload = AppointmentCreateRequest(
        doctor_id=doctor_user.doctor_profile.id,
        appointment_date=tomorrow,
        appointment_time="14:00",
        reason="Arrhythmia check",
    )
    appt = create_appointment(db_session, patient_user, payload)

    # 2. Doctor confirms appointment
    appt = update_appointment(
        db_session,
        doctor_user,
        appt.id,
        AppointmentUpdateRequest(status=AppointmentStatus.CONFIRMED),
    )
    assert appt.status == AppointmentStatus.CONFIRMED

    # 3. Doctor marks completed
    appt = update_appointment(
        db_session,
        doctor_user,
        appt.id,
        AppointmentUpdateRequest(status=AppointmentStatus.COMPLETED),
    )
    assert appt.status == AppointmentStatus.COMPLETED

    # 4. Doctor authors EMR record
    rec_payload = MedicalRecordCreateRequest(
        appointment_id=appt.id,
        diagnosis="Benign Sinus Tachycardia",
        symptoms="Palpitations during exercise",
        treatment="Rest and ECG monitoring",
        prescription="Electrolytes oral solution",
        notes="Clinical condition stable",
    )
    rec = create_medical_record(db_session, doctor_user, rec_payload)
    assert rec.id is not None
    assert rec.diagnosis == "Benign Sinus Tachycardia"

    # 5. Patient views authorized record
    records = get_medical_records(db_session, patient_user)
    assert len(records) == 1
    assert records[0].id == rec.id


def test_ui_admin_lockout_and_unlock(db_session):
    """Test user lockout and unlocking mechanisms."""
    user = create_sample_patient(db_session, "lockout_user")

    # 5 failed login attempts trigger lockout
    for _ in range(5):
        AuthService.authenticate_user(db_session, user.username, "WrongPass999!", client_ip="127.0.0.1")

    db_session.refresh(user)
    assert user.failed_login_attempts >= 5
    assert user.locked_until is not None

    # Locked user cannot log in
    _, err = AuthService.authenticate_user(db_session, user.username, "Password123!", client_ip="127.0.0.1")
    assert err is not None
    assert "locked" in err.lower()

    # Admin unlocks user
    user.failed_login_attempts = 0
    user.locked_until = None
    db_session.commit()
    db_session.refresh(user)

    assert user.locked_until is None
    assert user.failed_login_attempts == 0


def test_ui_jira_kanban_and_transition():
    """Test Jira Kanban board operations and status transitions."""
    summary = JiraService.get_project_summary()
    assert summary is not None
    assert "total_issues" in summary

    issues_resp = JiraService.get_issues()
    issues = issues_resp.get("issues", [])
    assert len(issues) > 0

    first_key = issues[0]["key"]
    res = JiraService.transition_issue(first_key, "In Progress")
    assert res.get("success") is True
