# SecureCare – Adaptive SDLC Framework for Secure Development of a Healthcare Management System

[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.1-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Atlassian Jira](https://img.shields.io/badge/Jira%20Cloud-REST%20v3-0052CC.svg)](https://www.atlassian.com/software/jira)
[![Tests](https://img.shields.io/badge/Pytest-82%2F82%20Passing-brightgreen.svg)]()
[![E2E Verification](https://img.shields.io/badge/E2E-26%2F26%20Passed-brightgreen.svg)]()

---

## 🌟 Executive Overview

**SecureCare** is an enterprise-grade Healthcare Management System (HMS) engineered under an **Adaptive Secure Software Development Life Cycle (SDLC)** framework. It delivers a modern, high-performance **React 18 SPA** (powered by Vite, Tailwind CSS, and Lucide Icons) backed by a high-assurance **FastAPI REST API**, **SQLAlchemy 2.0 ORM**, and **SQLite** database.

Rather than treating security as an isolated post-development audit, SecureCare integrates defensive threat-mitigation mechanisms iteratively into each agile sprint. In addition, the platform features a **live, bidirectional Atlassian Jira Cloud Integration** and project management telemetry.

### Sprints & Delivery Roadmap
* **Sprint 1 — Core Foundation, Database Modeling & Authentication**:
  SQLite relational schema, SQLAlchemy 2.0 ORM, secure salted `bcrypt` password hashing (12 work rounds), stateless HS256 JWT issuance and validation.
* **Sprint 2 — Appointment Lifecycle, RBAC & Clinical Dashboards**:
  State machine for appointments (Pending, Confirmed, Completed, Cancelled, Rejected), role-based access control (`ADMIN`, `DOCTOR`, `PATIENT`), schedule conflict detection, and doctor directories.
* **Sprint 3 — Medical Records, Prescriptions & Audit Trails**:
  Confidential electronic medical records (EMR), doctor clinical notes, prescriptions, diagnosis history, patient privacy boundaries, and automated tamper-evident audit logging.
* **Sprint 4 — Threat Defense, Account Lockout & Admin Governance**:
  Brute-force mitigation (automatic account lockout after 5 consecutive failed attempts for 15 minutes), IDOR prevention, administrative user/doctor approvals, security metric telemetry, and audit search.
* **Sprint 5 — Full System Integration, Jira Cloud & Modern React SPA**:
  Bidirectional Jira Cloud REST API integration, live Agile Kanban board, Sprints 1–5 velocity tracking, Epic traceability, and a modern React 18 + Tailwind CSS SaaS user interface.
* **Verified Quality Metrics**:
  * **Automated Pytest Suite**: **82 / 82 Passing (100% Pass Rate)**
  * **End-to-End (E2E) Integration Verification**: **26 / 26 Verification Steps Passed (100% Pass Rate)**
  * **Final Sprint 5 Validation & Security Benchmarks**: **100% Pass Rate (All endpoints sub-20ms latency)**

---

## 🎯 UN Sustainable Development Goal (SDG) Alignment

### Primary Goal: SDG 9 — Industry, Innovation, and Infrastructure
SecureCare aligns directly with **UN SDG 9 (Targets 9.c & 9.4)**:
* **Resilient Healthcare Digital Infrastructure**: Digital healthcare systems represent critical societal infrastructure. SecureCare safeguards patient services against disruption, credential stuffing, and data tampering.
* **Adaptive Secure SDLC Methodology**: Embeds continuous security practices (threat modeling, RBAC, tamper-evident audit trails, and automated test regression) into agile delivery cycles.
* **Enterprise Security Standards**: Implements defense-in-depth principles through stateless cryptographic JWT tokens, password hashing, automated sanitization, and continuous verification.

### Contextual Goal: SDG 3 — Good Health and Well-Being
Supports **UN SDG 3 (Target 3.8)**:
* Guarantees patient confidentiality and HIPAA-inspired privacy boundaries.
* Eliminates scheduling collisions and double-booking to optimize physician time.
* Ensures clinical integrity through immutable audit tracking for every consultation and prescription.

---

## 🏗️ System Architecture

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                               SECURECARE CLIENT INTERFACE                               │
 │                       Modern React 18 SPA (Vite + Tailwind CSS)                         │
 │                                                                                         │
 │   ┌────────────────────────┐  ┌─────────────────────────┐  ┌────────────────────────┐   │
 │   │  Auth & Persona Switch │  │ Role-Adaptive Portals   │  │ Jira Kanban & Sprints  │   │
 │   │  (Patient/Doctor/Admin)│  │ (Appointments & EMR)    │  │ (Velocity & Epics)     │   │
 │   └────────────────────────┘  └─────────────────────────┘  └────────────────────────┘   │
 └────────────────────────────────────────────┬────────────────────────────────────────────┘
                                              │ HTTP REST Requests (Axios via Vite Reverse Proxy)
                                              ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                               FASTAPI APPLICATION SERVER                                │
 │                                                                                         │
 │  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
 │  │                         Security & Authorization Dependencies                     │  │
 │  │  • JWT Bearer Validation     • Role-Based Access Control    • require_admin Guard │  │
 │  │  • Account Lockout Defense   • IDOR Isolation Verification  • CORS Middleware     │  │
 │  └─────────────────────────────────────────┬─────────────────────────────────────────┘  │
 │                                            │                                            │
 │        ┌───────────────────────────────────┼───────────────────────────────────┐        │
 │        ▼                                   ▼                                   ▼        │
 │  Domain Endpoints                 Administration APIs                Jira Cloud Proxy   │
 │  • /api/auth                      • /api/admin/users                 • /jira/status     │
 │  • /api/doctors                   • /api/admin/doctors               • /jira/project    │
 │  • /api/appointments              • /api/admin/audit-logs            • /jira/issues     │
 │  • /api/medical-records           • /api/admin/security-stats        • /jira/epics      │
 │  • /health, /api/health           • /docs, /redoc                    • /jira/sprints    │
 │        │                                   │                                   │        │
 │        └───────────────────────────────────┼───────────────────────────────────┘        │
 │                                            ▼                                            │
 │                                Business Services Layer                                  │
 │                                • AuthService (Registration & Brute-Force Guard)         │
 │                                • AppointmentService (Schedule Collision Guard)          │
 │                                • MedicalRecordService (Clinical Confidentiality)        │
 │                                • AuditService (Immutable Event Logging)                 │
 │                                • JiraService (Bidirectional Client & Fallback Cache)    │
 │                                            │                                            │
 │                                            ▼                                            │
 │                                SQLAlchemy 2.0 ORM Engine                                │
 └────────────────────────────────────────────┬────────────────────────────────────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
            SQLite Database (securecare.db)              Atlassian Jira Cloud (REST API v3)
          (Users, Patients, Doctors, Records,            https://sakec-team-bcq481n1.atlassian.net
             Appointments, Audit Logs)
```

---

## 🔒 Comprehensive Security Controls & Defensive Mechanisms

| Security Feature | Implementation Details | Threat Mitigated |
| :--- | :--- | :--- |
| **Stateless Authentication** | PyJWT with HS256 cryptographic signing and configurable TTL. | Session hijacking, replay attacks |
| **Password Protection** | Salted `bcrypt` hashing (12 work rounds). Plaintext passwords never stored. | Credential theft, rainbow table attacks |
| **Brute-Force Lockout** | Progressive counter tracks failed logins; locks account for 15 minutes after 5 failures. | Automated password spraying & brute-force |
| **Role-Based Access (RBAC)**| Granular server-side permission checks (`ADMIN`, `DOCTOR`, `PATIENT`). | Privilege escalation, unauthorized access |
| **Anti-IDOR Protection** | Server-side validation confirms ownership before medical records or appointments are modified. | Insecure Direct Object References (IDOR) |
| **Collision Prevention** | Database-level checking stops overlapping appointment slots for patients and doctors. | Schedule race conditions, double booking |
| **Audit Ledger** | Structured logging records IP, user ID, timestamp, and details for every security event. | Non-repudiation, compliance |

---

## 💻 Frontend Interface Architecture

### Modern React 18 Application (`frontend/`)
- **Single-Page Application**: Fluid tab transitions, instant micro-interactions, responsive modals, and zero page reloads.
- **Role-Adaptive User Portals**:
  - **Patient**: Health dashboard, upcoming consultation card, specialist directory with search filter, appointment booking modal with collision detection, and confidential EMR records.
  - **Doctor**: Clinical queue with one-click **Confirm** / **Reject**, confirmed schedule, and comprehensive **EMR Authoring Modal** for recording diagnoses, symptoms, treatments, and prescriptions.
  - **Admin**: Executive command center with KPI metrics, system health monitors, user IAM governance with one-click **Lockout Release**, physician availability toggle, searchable audit ledger with **instant CSV export**, and interactive **Jira Agile Kanban Board** with live status transitions.
- **Top Utility & Persona Switcher Banner**:
  - 1-click evaluation shortcuts to switch instantly between **Admin**, **Doctor**, and **Patient** personas.

---

## 🔄 Bidirectional Jira Cloud Integration

Integrated directly with Atlassian Jira Cloud (`https://sakec-team-bcq481n1.atlassian.net`):

* **Dynamic Project Discovery**: Reads project keys, issue types, and board schemas automatically.
* **Sprint Velocity & Burndown Tracker**: Real-time progress tracking for **Sprints 1 through 5**.
* **Epic Traceability Hub**: Visual breakdown of project epics with progress bars and child story states.
* **Interactive Kanban Board**:
  * 4 synchronized columns: **To Do**, **In Progress**, **In Review**, and **Done**.
  * Live status transitions executed directly from the SecureCare UI.
  * Direct modal/form to create and push new user stories/tasks to Jira Cloud.
* **Fault-Tolerant Caching**: Local caching ensures dashboard responsiveness during network outages or rate limiting.
* **Strict Admin Authorization**: Jira dashboards and status controls are accessible strictly to authenticated **`ADMIN`** users.

---

## 📁 Repository Structure

```text
├── frontend/                            # Modern React 18 SPA
│   ├── src/
│   │   ├── api/client.js                # Axios client with JWT bearer interceptor
│   │   ├── context/AuthContext.jsx      # Global auth state & 1-click persona switcher
│   │   ├── components/Navbar.jsx        # Navigation bar & persona banner
│   │   ├── pages/                       # Modular view components
│   │   │   ├── Login.jsx                # Split hero sign-in screen
│   │   │   ├── Register.jsx             # Patient self-registration form
│   │   │   ├── PatientDashboard.jsx     # Consultations, doctors & EMR viewer
│   │   │   ├── DoctorDashboard.jsx      # Clinical queue & EMR authoring
│   │   │   ├── AdminDashboard.jsx       # Executive KPIs, IAM, audit & Jira board
│   │   │   └── Documentation.jsx        # Architecture, SDG 9 & security matrix
│   │   ├── App.jsx                      # Main app shell & router
│   │   ├── main.jsx                     # Vite React entry point
│   │   └── index.css                    # Tailwind CSS directives
│   ├── Dockerfile                       # Multi-stage production Dockerfile (Node -> Nginx)
│   ├── nginx.conf                       # Production Nginx reverse proxy & SPA router
│   ├── .dockerignore                    # Frontend Docker ignore rules
│   ├── package.json                     # Frontend npm dependencies
│   ├── tailwind.config.js               # Tailwind design system tokens
│   └── vite.config.js                   # Vite reverse proxy config (/api -> 8000)
│
├── app/
│   ├── api/
│   │   ├── deps.py                      # Security dependencies (JWT auth, require_admin)
│   │   └── routes/                      # Modular REST endpoints
│   │       ├── admin.py                 # User management, audit logs & security telemetry
│   │       ├── appointments.py          # Appointment booking & collision guards
│   │       ├── auth.py                  # Login, registration, and lockout handling
│   │       ├── doctors.py               # Active doctor listing
│   │       ├── integrations.py          # Jira Cloud proxy & status transition endpoints
│   │       └── medical_records.py       # Confidential clinical records & doctor notes
│   ├── core/
│   │   ├── config.py                    # Environment settings (JWT, CORS, Lockout, Jira)
│   │   ├── permissions.py               # Role permission helpers
│   │   └── security.py                  # Bcrypt hashing and JWT token operations
│   ├── db/
│   │   ├── database.py                  # SQLAlchemy engine & SQLite connection session
│   │   └── session.py                   # Database session provider alias
│   ├── models/                          # Database ORM models
│   │   ├── appointment.py               # Appointment entity with state machine
│   │   ├── audit_log.py                 # Structured audit trail model
│   │   ├── doctor.py                    # Doctor profile and licensing
│   │   ├── medical_record.py            # Clinical diagnosis & prescription model
│   │   ├── patient.py                   # Patient demographic profile
│   │   └── user.py                      # User entity with lockout tracking
│   ├── schemas/                         # Pydantic validation schemas
│   ├── services/                        # Reusable business logic layer
│   ├── main.py                          # FastAPI REST API entry point
│   └── seed.py                          # Idempotent database seeder
│
├── compose.yaml                         # Docker Compose orchestration specification
├── Dockerfile.backend                   # Production hardened FastAPI container image
├── docker-entrypoint.sh                 # Backend initialization & auto-seeding entrypoint
├── .dockerignore                        # Root Docker ignore rules
├── tests/                               # Pytest automated test suite (82 Tests)
│   ├── conftest.py                      # TestClient fixtures and in-memory database
│   ├── test_admin.py                    # Admin RBAC and user lifecycle tests
│   ├── test_appointments.py             # Appointment state machine and collision tests
│   ├── test_auth.py                     # Authentication and password hashing tests
│   ├── test_jira.py                     # Jira Cloud integration and sync tests
│   ├── test_medical_records.py          # Medical record privacy and audit log tests
│   ├── test_security.py                 # Brute-force lockout and security tests
│   └── test_ui.py                       # UI workflow & lifecycle tests
│
├── .env.example                         # Environment configuration template
├── requirements.txt                     # Pinned Python dependencies (FastAPI, SQLAlchemy, PyJWT)
├── verify_sprint4_e2e.py                # 26-step automated end-to-end integration test
├── verify_sprint5_final.py              # Sprint 5 performance benchmark & security suite
└── README.md                            # Complete system documentation
```

---

## 🔑 Default Credentials for Evaluation

| Role | Username / Email | Password | Access Highlights |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` / `admin@securecare.org` | `AdminSecure123!` | Executive KPIs, IAM Governance, Audit Ledger, **Jira Kanban Board** |
| **Doctor** | `dr_priya` / `priya.sharma@securecare.local` | `DoctorSecure123!` | Clinical Queue, Confirm/Reject, Schedule, Author EMR & Prescriptions |
| **Patient** | `manual_patient` / `manual_patient@testcare.org` | `PatientSecure123!` | Specialist Directory, Booking Form, Collision Guard, Medical Records |

*(The top navigation bar also includes 1-click **🛡️ Admin**, **🩺 Doctor**, and **👤 Patient** buttons for instant persona switching).*

---

## 🐳 Basic Docker Setup

SecureCare provides a clean, straightforward, single-stage Docker configuration that is easy to understand, maintain, and grade.

### Architecture Overview

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      DOCKER HOST (localhost:5173 / 8080)               │
 │                                                                        │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │               Frontend Service (securecare-frontend)             │  │
 │  │        • Clean single-stage image based on node:20-alpine        │  │
 │  │        • Runs Vite server with hot reloading & SPA routing       │  │
 │  │        • Internal proxy routing:                                 │  │
 │  │          - /api/* -> http://backend:8000/api/*                   │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 │                                     │ Docker Network                   │
 │                                     ▼                                  │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                Backend Service (securecare-backend)              │  │
 │  │        • Clean single-stage image based on python:3.11-slim      │  │
 │  │        • Auto database seed on start (python -m app.seed)        │  │
 │  │        • Uvicorn ASGI server listening on 0.0.0.0:8000           │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 │                                     │ Mounted Volume                   │
 │                                     ▼                                  │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │    Named Persistent Volume (securecare_backend_data -> /data)    │  │
 │  │    • Preserves SQLite database (securecare.db) across restarts   │  │
 │  └──────────────────────────────────────────────────────────────────┘  │
 └────────────────────────────────────────────────────────────────────────┘
```

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- Docker Compose v2 (included with Docker Desktop).

### 2. Environment Configuration
Copy the sample environment file if not already present:
```powershell
cp .env.example .env
```

### 3. Build & Run Containers
Launch all services in detached mode:
```powershell
docker compose up --build -d
```

### 4. Application Access Points
Once started, access the platform at:
* **Web Application UI**: [http://localhost:5173/](http://localhost:5173/) or [http://localhost:8080/](http://localhost:8080/)
* **Backend REST API & Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health) or [http://localhost:5173/api/health](http://localhost:5173/api/health)

### 5. Essential Docker Management Commands
```powershell
# View running container status and health
docker compose ps

# View live container logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# Verify database file inside persistent volume
docker compose exec backend ls -la /data

# Stop all running containers gracefully
docker compose down

# Stop containers and remove persistent volume (clean reset)
docker compose down -v
```

---

## 🚀 Local Development Quickstart (Windows PowerShell)

### 1. Prerequisites
* Python 3.10+
* Node.js 18+ (Node v22 installed)
* Git

### 2. Environment Setup
```powershell
# Clone or navigate to project repository
cd "C:\PROJECTS\Healthcare Management System"

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python backend dependencies
pip install -r requirements.txt

# Install React frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Environment Configuration (`.env`)
Create or verify your `.env` file in the root directory (copy from `.env.example`):
```ini
PROJECT_NAME="SecureCare Healthcare Management System"
VERSION="1.0.0"
API_V1_STR="/api"
DATABASE_URL="sqlite:///./securecare.db"
SECRET_KEY="c83f942ba621980ee9d41e73797c5fba609f25efd03158c3534e75d1d4d39f4a"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
ALLOWED_ORIGINS=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5173", "http://127.0.0.1:5173"]

# Jira Cloud Configuration
JIRA_BASE_URL="https://sakec-team-bcq481n1.atlassian.net"
JIRA_EMAIL="your-atlassian-account@example.com"
JIRA_API_TOKEN="your-atlassian-api-token"
JIRA_PROJECT_KEY="SCR"
```

### 4. Initialize Database
```powershell
python -m app.seed
```

### 5. Launch the Application

#### Step 1: Start FastAPI REST Backend Server
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Technical Specifications**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Step 2: Start Modern React Frontend
```powershell
cd frontend
npm run dev
```
* **React Web Application**: [http://localhost:5173/](http://localhost:5173/) *(Proxies `/api` directly to backend)*

---

## 🧪 Automated Testing & Verification

### 1. Run Full Pytest Suite (82 Tests)
```powershell
pytest -v
```
```text
================== 82 passed, 1 warning in 107.41s (0:01:47) ==================
```

### 2. Run End-to-End Workflow Verification (26 Steps)
```powershell
python verify_sprint4_e2e.py
```
```text
==================================================
E2E VERIFICATION COMPLETE: 26/26 PASSED
==================================================
```

### 3. Run Sprint 5 Final Security & Benchmark Validation
```powershell
python verify_sprint5_final.py
```
```text
======================================================================
ALL SPRINT 5 INTEGRATION & SECURITY VALIDATIONS: PASSED
======================================================================
```
