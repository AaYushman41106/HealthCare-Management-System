# SecureCare – Adaptive SDLC Framework for Secure Development of a Healthcare Management System

## Sprint 1: Foundation, Data Models & Secure Authentication

SecureCare is an enterprise-grade healthcare management system developed following an **Adaptive Secure Software Development Life Cycle (SDLC)** framework. Sprint 1 focuses exclusively on establishing a hardened foundational architecture, database modeling, secure authentication, and authorization boundaries.

---

## 🌟 Tech Stack

* **Backend Framework**: Python FastAPI (Asynchronous, High-Performance)
* **Database**: SQLite
* **Object-Relational Mapping (ORM)**: SQLAlchemy 2.0
* **Authentication**: JSON Web Tokens (JWT) via PyJWT
* **Password Hashing**: Bcrypt (salted, 12 rounds)
* **Validation & Schemas**: Pydantic v2 & Pydantic Settings
* **Frontend**: Vanilla HTML5, CSS3, JavaScript (Responsive Healthcare UI & API Inspector)
* **Interactive API Documentation**: Swagger UI (`/docs`) & ReDoc (`/redoc`)
* **Automated Testing**: Pytest & HTTPX TestClient

---

## 📁 Project Structure

```text
Healthcare Management System/
│
├── .env.example              # Environment variables template
├── .env                      # Local environment configuration (ignored by git)
├── .gitignore                # Git ignore rules for venv, caches, db, env
├── requirements.txt          # Python project dependencies
├── README.md                 # Complete project documentation
├── securecare.db             # Auto-generated SQLite database
│
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application setup, CORS, lifespan DB init
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Pydantic Settings configuration loader
│   │   └── security.py       # Bcrypt password hashing & JWT encoding/decoding
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py       # SQLAlchemy engine, session maker, get_db, init_db
│   ├── models/
│   │   ├── __init__.py       # Model registry export
│   │   ├── user.py           # User entity and UserRole enum (PATIENT, DOCTOR, ADMIN)
│   │   ├── patient.py        # Patient entity and profile relationship
│   │   └── doctor.py         # Doctor entity and profile relationship
│   ├── schemas/
│   │   ├── __init__.py       # Schema exports
│   │   └── auth.py           # Registration, Login, Token, and UserResponse schemas
│   └── api/
│       ├── __init__.py
│       ├── deps.py           # JWT extraction and validation dependency (get_current_user)
│       └── routes/
│           ├── __init__.py   # Sub-router registry
│           └── auth.py       # Endpoints: /register, /login, /me
│
├── static/
│   ├── index.html            # Web interface with Register, Login, and Profile views
│   ├── css/
│   │   └── styles.css        # Healthcare UI design and styling
│   └── js/
│       └── app.js            # Frontend logic, JWT storage, and live API console
│
└── tests/
    ├── __init__.py
    ├── conftest.py           # In-memory SQLite fixtures and TestClient configuration
    └── test_auth.py          # 9 automated security & authentication tests
```

---

## 🔐 Security Controls Implemented (Sprint 1)

1. **Robust Password Hashing**: Passwords are never stored in plaintext. They are salted and hashed using `bcrypt` (12 rounds) before persisting to the database.
2. **Stateless JWT Authentication**: Issues cryptographically signed HS256 tokens with expiration timestamps (`exp`) and subject user identifiers (`sub`).
3. **Privilege Escalation Protection**: Public registration defaults to `PATIENT`. Any attempts to supply `ADMIN` or `DOCTOR` during public registration are rejected with a 400 Bad Request / 422 Unprocessable Entity error.
4. **Safe Error Messages**: Login rejects invalid usernames or passwords using a generic message (`Invalid username or password`) to mitigate user enumeration attacks.
5. **No Password Hash Leakage**: The `GET /api/auth/me` endpoint returns sanitized user details (`id`, `username`, `email`, `role`, `is_active`, `created_at`) and explicitly excludes `hashed_password`.
6. **SQL Injection Mitigation**: All database operations use the SQLAlchemy ORM abstraction layer; no raw string concatenated SQL queries.
7. **Environment-Driven Secrets**: All secrets (`SECRET_KEY`, `ALGORITHM`, `DATABASE_URL`) are read from `.env` via `pydantic-settings`, with no hardcoded secrets in source files.
8. **Automated Schema Provisioning**: Database tables are initialized automatically on application startup via FastAPI lifespan events.

---

## 🚀 Setup & Execution Guide (Windows 11 / PowerShell)

### 1. Prerequisites
* Windows 11
* Python 3.10+ (tested on Python 3.13)
* PowerShell or VS Code Terminal

### 2. Set Up Virtual Environment
```powershell
# Navigate to the project root
cd "C:\PROJECTS\Healthcare Management System"

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (already done by default for local development):
```powershell
Copy-Item .env.example .env
```

### 5. Run the Application
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
* **Web Application Interface**: Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in any modern browser.
* **Interactive Swagger UI**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
* **ReDoc Documentation**: Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```powershell
pytest -v
```

### Sprint 1 Test Coverage:
1. `test_successful_registration`: Validates user registration with default `PATIENT` role and sanitization.
2. `test_duplicate_registration`: Confirms duplicate username or email requests are rejected.
3. `test_successful_login`: Confirms successful credential verification and token issuance.
4. `test_invalid_login`: Verifies safe error handling without username/password enumeration.
5. `test_access_me_with_valid_token`: Validates access to `GET /api/auth/me` with valid JWT and verifies no password hash leakage.
6. `test_access_me_without_token`: Verifies 401 Unauthorized when no Authorization header is provided.
7. `test_access_me_invalid_token`: Verifies 401 Unauthorized when a malformed or forged token is provided.
8. `test_passwords_are_stored_hashed`: Directly inspects the database to ensure stored password begins with bcrypt prefix and matches verification.
9. `test_admin_cannot_be_created_publicly`: Verifies attempts to register as `ADMIN` or `DOCTOR` publicly fail and no unauthorized admin records exist.

---

## 📡 API Endpoints Implemented

| Method | Endpoint | Access | Description | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/register` | Public | Register new patient account (hashes password, defaults role to PATIENT) | `201 Created` |
| **POST** | `/api/auth/login` | Public | Authenticate user & issue signed JWT access token | `200 OK` |
| **GET** | `/api/auth/me` | Authenticated | Retrieve profile for current user (excludes password) | `200 OK` |
| **GET** | `/health` | Public | System health check endpoint | `200 OK` |
| **GET** | `/docs` | Public | Interactive OpenAPI / Swagger UI | `200 OK` |

---

## ⚠️ Known Limitations (Scope of Sprint 1)

As specified by the project requirements, Sprint 1 implements the foundational secure authentication framework and database models. The following features are intentionally out of scope and will be delivered in subsequent sprints:
* Appointment scheduling and doctor availability
* Medical records, prescriptions, and lab reports
* Doctor/Admin administrative dashboards
* Refresh tokens and token revocation/blocklists
* Audit logging and SIEM integration
