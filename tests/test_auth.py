from app.core.security import verify_password
from app.models.user import User, UserRole


def test_successful_registration(client):
    """Test 1: Successful registration with valid data and default PATIENT role."""
    payload = {
        "username": "alice_smith",
        "email": "alice@example.com",
        "password": "Password123!",
        "full_name": "Alice Smith",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["username"] == "alice_smith"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "PATIENT"
    assert data["is_active"] is True
    assert "id" in data
    # Ensure sensitive credentials are never returned
    assert "password" not in data
    assert "hashed_password" not in data


def test_duplicate_registration(client):
    """Test 2: Prevent duplicate registrations for existing username or email."""
    payload = {
        "username": "bob_jones",
        "email": "bob@example.com",
        "password": "Password123!",
    }
    # Initial registration
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt duplicate username
    res_dup_username = client.post("/api/auth/register", json={
        "username": "bob_jones",
        "email": "different@example.com",
        "password": "Password123!",
    })
    assert res_dup_username.status_code == 400
    assert "already registered" in res_dup_username.json()["detail"].lower()

    # Attempt duplicate email
    res_dup_email = client.post("/api/auth/register", json={
        "username": "different_bob",
        "email": "bob@example.com",
        "password": "Password123!",
    })
    assert res_dup_email.status_code == 400
    assert "already registered" in res_dup_email.json()["detail"].lower()


def test_successful_login(client):
    """Test 3: Successful login returning a signed JWT access token and user role."""
    # Register first
    client.post("/api/auth/register", json={
        "username": "carol_danvers",
        "email": "carol@example.com",
        "password": "Password123!",
    })

    # Login
    response = client.post("/api/auth/login", json={
        "username": "carol_danvers",
        "password": "Password123!",
    })
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "PATIENT"
    assert len(data["access_token"]) > 20


def test_invalid_login(client):
    """Test 4: Invalid login credentials safely rejected without leaking specific account existence."""
    # Register user
    client.post("/api/auth/register", json={
        "username": "david_h",
        "email": "david@example.com",
        "password": "CorrectPassword123!",
    })

    # Wrong password
    res_wrong_pw = client.post("/api/auth/login", json={
        "username": "david_h",
        "password": "WrongPassword999!",
    })
    assert res_wrong_pw.status_code == 401
    assert res_wrong_pw.json()["detail"] == "Invalid username or password"

    # Non-existent user
    res_non_existent = client.post("/api/auth/login", json={
        "username": "ghost_user",
        "password": "SomePassword123!",
    })
    assert res_non_existent.status_code == 401
    assert res_non_existent.json()["detail"] == "Invalid username or password"


def test_access_me_with_valid_token(client):
    """Test 5: Accessing /api/auth/me with a valid token returns sanitized user information."""
    client.post("/api/auth/register", json={
        "username": "emma_watson",
        "email": "emma@example.com",
        "password": "Password123!",
    })

    login_res = client.post("/api/auth/login", json={
        "username": "emma_watson",
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["username"] == "emma_watson"
    assert data["email"] == "emma@example.com"
    assert data["role"] == "PATIENT"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_access_me_without_token(client):
    """Test 6: Accessing /api/auth/me without an Authorization token is rejected."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


def test_access_me_invalid_token(client):
    """Test 7: Accessing /api/auth/me with an invalid/tampered token is rejected."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


def test_passwords_are_stored_hashed(client, db_session):
    """Test 8: Verify that passwords are never stored in plaintext and use bcrypt hashing."""
    plain_password = "SecretPassword123!"
    client.post("/api/auth/register", json={
        "username": "frank_miller",
        "email": "frank@example.com",
        "password": plain_password,
    })

    user = db_session.query(User).filter(User.username == "frank_miller").first()
    assert user is not None
    # Password must not be plaintext
    assert user.hashed_password != plain_password
    # Password must start with bcrypt prefix ($2b$ or $2a$)
    assert user.hashed_password.startswith("$2")
    # Verifiable with bcrypt
    assert verify_password(plain_password, user.hashed_password) is True
    assert verify_password("WrongPassword123!", user.hashed_password) is False


def test_admin_cannot_be_created_publicly(client, db_session):
    """Test 9: Verify ADMIN and DOCTOR roles cannot be created through public registration."""
    # Attempt to pass ADMIN role in registration payload
    admin_payload = {
        "username": "hacker_admin",
        "email": "hacker@example.com",
        "password": "Password123!",
        "role": "ADMIN",
    }
    response = client.post("/api/auth/register", json=admin_payload)
    # Must be rejected (either 400 or 422 validation failure)
    assert response.status_code in (400, 422)

    # Attempt to pass DOCTOR role in registration payload
    doctor_payload = {
        "username": "fake_doctor",
        "email": "doctor@example.com",
        "password": "Password123!",
        "role": "DOCTOR",
    }
    doc_response = client.post("/api/auth/register", json=doctor_payload)
    assert doc_response.status_code in (400, 422)

    # Verify no ADMIN or DOCTOR was inserted into database
    admin_user = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    assert admin_user is None

    doctor_user = db_session.query(User).filter(User.role == UserRole.DOCTOR).first()
    assert doctor_user is None
