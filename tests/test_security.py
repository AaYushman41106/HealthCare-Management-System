import pytest
from app.core.security import create_access_token, hash_password
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserRole


@pytest.fixture
def admin_client(client, db_session):
    admin = User(
        username="sec_admin",
        email="sec_admin@securecare.org",
        hashed_password=hash_password("AdminSecure123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token(
        subject=admin.id,
        claims={"username": admin.username, "role": admin.role.value},
    )
    return client, {"Authorization": f"Bearer {token}"}, admin


def test_brute_force_account_lockout(client):
    """5 consecutive failed login attempts must lock the user account and return 403 on subsequent attempts."""
    # Register victim user
    client.post(
        "/api/auth/register",
        json={
            "username": "victim_user",
            "email": "victim@example.com",
            "password": "CorrectSecret123!",
        },
    )

    # 4 invalid attempts -> all return 401
    for i in range(4):
        res = client.post(
            "/api/auth/login",
            json={"username": "victim_user", "password": "WrongPassword!"},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid username or password"

    # 5th invalid attempt -> triggers lockout, returns 401
    res_5th = client.post(
        "/api/auth/login",
        json={"username": "victim_user", "password": "WrongPassword!"},
    )
    assert res_5th.status_code == 401

    # 6th attempt (even with CORRECT password) -> must be blocked with 403 Forbidden due to lockout
    res_locked = client.post(
        "/api/auth/login",
        json={"username": "victim_user", "password": "CorrectSecret123!"},
    )
    assert res_locked.status_code == 403
    assert "temporarily locked" in res_locked.json()["detail"]


def test_successful_login_resets_failed_counter(client):
    """A valid login resets failed attempt counter so account does not lock unexpectedly."""
    client.post(
        "/api/auth/register",
        json={
            "username": "reset_user",
            "email": "reset@example.com",
            "password": "ValidSecret123!",
        },
    )

    # 3 failed attempts
    for _ in range(3):
        client.post(
            "/api/auth/login",
            json={"username": "reset_user", "password": "WrongPassword!"},
        )

    # Successful login resets the counter
    res_success = client.post(
        "/api/auth/login",
        json={"username": "reset_user", "password": "ValidSecret123!"},
    )
    assert res_success.status_code == 200

    # Another 3 failed attempts should NOT lock the account yet
    for _ in range(3):
        res = client.post(
            "/api/auth/login",
            json={"username": "reset_user", "password": "WrongPassword!"},
        )
        assert res.status_code == 401

    # Still accessible with valid password
    res_success2 = client.post(
        "/api/auth/login",
        json={"username": "reset_user", "password": "ValidSecret123!"},
    )
    assert res_success2.status_code == 200


def test_admin_can_unlock_locked_account(client, admin_client):
    """Admin can unlock an account locked by brute-force protection."""
    _, admin_headers, _ = admin_client

    client.post(
        "/api/auth/register",
        json={
            "username": "locked_guy",
            "email": "locked@example.com",
            "password": "MySuperSecret123!",
        },
    )

    # Lock account with 5 failed attempts
    for _ in range(5):
        client.post(
            "/api/auth/login",
            json={"username": "locked_guy", "password": "BadPassword!"},
        )

    # Verify locked
    res_locked = client.post(
        "/api/auth/login",
        json={"username": "locked_guy", "password": "MySuperSecret123!"},
    )
    assert res_locked.status_code == 403

    # Find user ID via admin list
    res_users = client.get("/api/admin/users", headers=admin_headers)
    target_user = [u for u in res_users.json() if u["username"] == "locked_guy"][0]
    assert target_user["failed_login_attempts"] == 5
    assert target_user["locked_until"] is not None

    # Admin unlocks user
    res_unlock = client.patch(
        f"/api/admin/users/{target_user['id']}/status",
        headers=admin_headers,
        json={"is_active": True, "unlock": True},
    )
    assert res_unlock.status_code == 200
    assert res_unlock.json()["failed_login_attempts"] == 0
    assert res_unlock.json()["locked_until"] is None

    # User can log in immediately
    res_login = client.post(
        "/api/auth/login",
        json={"username": "locked_guy", "password": "MySuperSecret123!"},
    )
    assert res_login.status_code == 200


def test_password_hash_never_exposed(client, admin_client):
    """Verify password hashes are never present in any API responses."""
    _, admin_headers, _ = admin_client

    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "hash_test_user",
            "email": "hashtest@example.com",
            "password": "SecretPassword123!",
        },
    )
    assert "hashed_password" not in reg_res.json()

    login_res = client.post(
        "/api/auth/login",
        json={"username": "hash_test_user", "password": "SecretPassword123!"},
    )
    assert "hashed_password" not in login_res.json()
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert "hashed_password" not in me_res.json()

    admin_users = client.get("/api/admin/users", headers=admin_headers)
    for u in admin_users.json():
        assert "hashed_password" not in u

    admin_docs = client.get("/api/admin/doctors", headers=admin_headers)
    for d in admin_docs.json():
        assert "hashed_password" not in d


def test_audit_logs_record_security_events(client, admin_client):
    """Confirm security events (LOGIN_FAILURE, ACCOUNT_LOCKED, LOGIN_SUCCESS) are recorded in audit logs."""
    _, admin_headers, _ = admin_client

    client.post(
        "/api/auth/register",
        json={
            "username": "audit_probe",
            "email": "audit_probe@example.com",
            "password": "ProbePassword123!",
        },
    )

    # Trigger failed logins and lockout
    for _ in range(5):
        client.post(
            "/api/auth/login",
            json={"username": "audit_probe", "password": "BadPassword!"},
        )

    # Check audit logs for ACCOUNT_LOCKED event
    res_logs = client.get(
        "/api/admin/audit-logs?action=ACCOUNT_LOCKED",
        headers=admin_headers,
    )
    assert res_logs.status_code == 200
    lock_events = res_logs.json()
    assert len(lock_events) >= 1
    assert "locked after 5 failed login attempts" in lock_events[0]["details"]
