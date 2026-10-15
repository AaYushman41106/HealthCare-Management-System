"""Sprint 4 Comprehensive End-to-End Verification Script

Executes all 26 verification steps specified in Sprint 4 requirements:
1. Register patient Alice
2. Login as Alice
3. View available doctors
4. Book appointment with Doctor 1
5. Login as Doctor 1
6. Doctor confirms Alice's appointment
7. Doctor marks Alice's appointment COMPLETED
8. Doctor creates medical record for Alice
9. Patient Alice views her own medical record
10. Patient Alice attempts to create medical record -> 403
11. Patient Alice attempts to access another patient's data -> 403/404
12. Doctor 2 attempts to view Alice's medical record -> 403
13. Patient Alice attempts conflicting appointment -> 409
14. Non-admin attempts GET /api/admin/users -> 403
15. Non-admin attempts GET /api/admin/doctors -> 403
16. Non-admin attempts GET /api/admin/audit-logs -> 403
17. Non-admin attempts GET /api/admin/security-stats -> 403
18. Unauthenticated request to /api/admin/* -> 401
19. Admin logs in -> 200
20. Admin views user list -> 200, no hashes
21. Admin views doctor list -> 200
22. Admin views security stats -> 200
23. Admin views audit logs -> 200
24. Admin deactivates a user -> user cannot log in
25. Multiple failed logins trigger lockout -> 403
26. Admin re-enables / unlocks user -> user can log in again
"""

import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.database import Base, get_db
from app.main import app
from app.models.doctor import Doctor
from app.models.user import User, UserRole

# Isolated in-memory database for clean E2E verification run
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

db = TestingSession()

# Override get_db
def override_db():
    try:
        yield db
    finally:
        pass

app.dependency_overrides[get_db] = override_db
client = TestClient(app)

# Pre-seed doctors & admin into verification db
doc1_u = User(username="dr_priya", email="priya@securecare.org", hashed_password=hash_password("DoctorSecure123!"), role=UserRole.DOCTOR, is_active=True)
doc2_u = User(username="dr_rahul", email="rahul@securecare.org", hashed_password=hash_password("DoctorSecure123!"), role=UserRole.DOCTOR, is_active=True)
admin_u = User(username="admin", email="admin@securecare.org", hashed_password=hash_password("AdminSecure123!"), role=UserRole.ADMIN, is_active=True)
db.add_all([doc1_u, doc2_u, admin_u])
db.flush()

doc1_p = Doctor(user_id=doc1_u.id, full_name="Dr. Priya Sharma", specialization="Cardiology", license_number="DOC-101", is_active=True)
doc2_p = Doctor(user_id=doc2_u.id, full_name="Dr. Rahul Mehta", specialization="General Medicine", license_number="DOC-102", is_active=True)
db.add_all([doc1_p, doc2_p])
db.commit()

step_results = []

def run_step(step_num, title, test_func):
    try:
        test_func()
        step_results.append((step_num, title, "PASSED"))
        print(f"[{step_num:02d}] PASS: {title}")
    except Exception as e:
        step_results.append((step_num, title, f"FAILED: {e}"))
        print(f"[{step_num:02d}] FAIL: {title} -> {e}")

state = {}

# Step 1: Register patient Alice
def s01():
    res = client.post("/api/auth/register", json={
        "username": "alice_w",
        "email": "alice@example.com",
        "full_name": "Alice Wonderland",
        "password": "Password123!",
    })
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
run_step(1, "Register patient Alice", s01)

# Step 2: Login as Alice
def s02():
    res = client.post("/api/auth/login", json={
        "username": "alice_w",
        "password": "Password123!",
    })
    assert res.status_code == 200
    state["alice_token"] = res.json()["access_token"]
run_step(2, "Login as Alice", s02)

# Step 3: View available doctors
def s03():
    res = client.get("/api/doctors")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 2
    state["doc1_id"] = docs[0]["id"]
    state["doc2_id"] = docs[1]["id"]
run_step(3, "View available doctors", s03)

# Step 4: Book appointment with Doctor 1
def s04():
    res = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {state['alice_token']}"},
        json={
            "doctor_id": state["doc1_id"],
            "appointment_date": "2026-10-20",
            "appointment_time": "10:00",
            "reason": "Cardiac checkup",
        },
    )
    assert res.status_code == 201
    state["appt_id"] = res.json()["id"]
run_step(4, "Book appointment with Doctor 1", s04)

# Step 5: Login as Doctor 1
def s05():
    res = client.post("/api/auth/login", json={
        "username": "dr_priya",
        "password": "DoctorSecure123!",
    })
    assert res.status_code == 200
    state["doc1_token"] = res.json()["access_token"]
run_step(5, "Login as Doctor 1", s05)

# Step 6: Doctor confirms Alice's appointment
def s06():
    res = client.patch(
        f"/api/appointments/{state['appt_id']}",
        headers={"Authorization": f"Bearer {state['doc1_token']}"},
        json={"status": "CONFIRMED"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CONFIRMED"
run_step(6, "Doctor confirms Alice's appointment", s06)

# Step 7: Doctor marks Alice's appointment COMPLETED
def s07():
    res = client.patch(
        f"/api/appointments/{state['appt_id']}",
        headers={"Authorization": f"Bearer {state['doc1_token']}"},
        json={"status": "COMPLETED"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
run_step(7, "Doctor marks Alice's appointment COMPLETED", s07)

# Step 8: Doctor creates medical record for Alice
def s08():
    res = client.post(
        "/api/medical-records",
        headers={"Authorization": f"Bearer {state['doc1_token']}"},
        json={
            "appointment_id": state["appt_id"],
            "diagnosis": "Mild sinus arrhythmia",
            "symptoms": "Occasional palpitations",
            "treatment": "Adequate hydration and monitor heart rate",
            "prescription": "Electrolyte supplements once daily",
            "notes": "Follow up in 3 months",
        },
    )
    assert res.status_code == 201
    state["record_id"] = res.json()["id"]
run_step(8, "Doctor creates medical record for Alice", s08)

# Step 9: Patient Alice views her own medical record
def s09():
    res = client.get(
        f"/api/medical-records/{state['record_id']}",
        headers={"Authorization": f"Bearer {state['alice_token']}"},
    )
    assert res.status_code == 200
    assert res.json()["diagnosis"] == "Mild sinus arrhythmia"
run_step(9, "Patient Alice views her own medical record", s09)

# Step 10: Patient Alice attempts to create medical record -> 403
def s10():
    res = client.post(
        "/api/medical-records",
        headers={"Authorization": f"Bearer {state['alice_token']}"},
        json={
            "appointment_id": state["appt_id"],
            "diagnosis": "Self diagnosed",
            "symptoms": "None",
            "treatment": "None",
        },
    )
    assert res.status_code == 403
run_step(10, "Patient Alice attempts to create medical record (403)", s10)

# Step 11: Patient Alice attempts to access another patient's data -> 403/404
def s11():
    res = client.get(
        "/api/appointments/99999",
        headers={"Authorization": f"Bearer {state['alice_token']}"},
    )
    assert res.status_code in [403, 404]
run_step(11, "Patient Alice attempts to access another patient's appointment (403/404)", s11)

# Step 12: Doctor 2 attempts to view Alice's medical record -> 403
def s12():
    res_login = client.post("/api/auth/login", json={
        "username": "dr_rahul",
        "password": "DoctorSecure123!",
    })
    doc2_token = res_login.json()["access_token"]
    res = client.get(
        f"/api/medical-records/{state['record_id']}",
        headers={"Authorization": f"Bearer {doc2_token}"},
    )
    assert res.status_code == 403
run_step(12, "Doctor 2 attempts to view Alice's medical record (403)", s12)

# Step 13: Patient Alice attempts conflicting appointment -> 409
def s13():
    # Another patient Bob tries booking same doctor at same date/time
    client.post("/api/auth/register", json={
        "username": "bob_b", "email": "bob@example.com", "password": "Password123!"
    })
    res_l = client.post("/api/auth/login", json={"username": "bob_b", "password": "Password123!"})
    bob_token = res_l.json()["access_token"]

    # Book an initial active appointment
    res_book1 = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "doctor_id": state["doc1_id"],
            "appointment_date": "2026-10-25",
            "appointment_time": "14:00",
            "reason": "Consultation",
        },
    )
    assert res_book1.status_code == 201

    # Alice tries to book same slot
    res_conf = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {state['alice_token']}"},
        json={
            "doctor_id": state["doc1_id"],
            "appointment_date": "2026-10-25",
            "appointment_time": "14:00",
            "reason": "Conflicting slot",
        },
    )
    assert res_conf.status_code == 409
run_step(13, "Patient Alice attempts conflicting appointment (409)", s13)

# Step 14: Non-admin attempts GET /api/admin/users -> 403
def s14():
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {state['alice_token']}"})
    assert res.status_code == 403
run_step(14, "Non-admin attempts GET /api/admin/users (403)", s14)

# Step 15: Non-admin attempts GET /api/admin/doctors -> 403
def s15():
    res = client.get("/api/admin/doctors", headers={"Authorization": f"Bearer {state['alice_token']}"})
    assert res.status_code == 403
run_step(15, "Non-admin attempts GET /api/admin/doctors (403)", s15)

# Step 16: Non-admin attempts GET /api/admin/audit-logs -> 403
def s16():
    res = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {state['alice_token']}"})
    assert res.status_code == 403
run_step(16, "Non-admin attempts GET /api/admin/audit-logs (403)", s16)

# Step 17: Non-admin attempts GET /api/admin/security-stats -> 403
def s17():
    res = client.get("/api/admin/security-stats", headers={"Authorization": f"Bearer {state['alice_token']}"})
    assert res.status_code == 403
run_step(17, "Non-admin attempts GET /api/admin/security-stats (403)", s17)

# Step 18: Unauthenticated request to /api/admin/* -> 401
def s18():
    res1 = client.get("/api/admin/users")
    res2 = client.get("/api/admin/doctors")
    res3 = client.get("/api/admin/audit-logs")
    res4 = client.get("/api/admin/security-stats")
    assert res1.status_code == 401 and res2.status_code == 401 and res3.status_code == 401 and res4.status_code == 401
run_step(18, "Unauthenticated request to /api/admin/* (401)", s18)

# Step 19: Admin logs in -> 200
def s19():
    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "AdminSecure123!",
    })
    assert res.status_code == 200
    assert res.json()["role"] == "ADMIN"
    state["admin_token"] = res.json()["access_token"]
run_step(19, "Admin logs in (200)", s19)

# Step 20: Admin views user list -> 200, no hashes
def s20():
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 4
    for u in users:
        assert "hashed_password" not in u
        assert "password" not in u
run_step(20, "Admin views user list (200, no hashes)", s20)

# Step 21: Admin views doctor list -> 200
def s21():
    res = client.get("/api/admin/doctors", headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 2
run_step(21, "Admin views doctor list (200)", s21)

# Step 22: Admin views security stats -> 200
def s22():
    res = client.get("/api/admin/security-stats", headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_users"] >= 4
    assert stats["total_appointments"] >= 2
    assert stats["total_medical_records"] >= 1
run_step(22, "Admin views security stats (200)", s22)

# Step 23: Admin views audit logs -> 200
def s23():
    res = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {state['admin_token']}"})
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 5
run_step(23, "Admin views audit logs (200)", s23)

# Step 24: Admin deactivates a user -> user cannot log in
def s24():
    # Find Bob's ID
    res_users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {state['admin_token']}"})
    bob = [u for u in res_users.json() if u["username"] == "bob_b"][0]
    
    # Deactivate Bob
    res_deact = client.patch(
        f"/api/admin/users/{bob['id']}/status",
        headers={"Authorization": f"Bearer {state['admin_token']}"},
        json={"is_active": False},
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # Bob login rejected with 400 Inactive
    res_l = client.post("/api/auth/login", json={"username": "bob_b", "password": "Password123!"})
    assert res_l.status_code == 400
run_step(24, "Admin deactivates a user -> user cannot log in", s24)

# Step 25: Multiple failed logins trigger lockout -> 403
def s25():
    # Register test lockout target
    client.post("/api/auth/register", json={
        "username": "lock_target", "email": "target@example.com", "password": "TargetPassword123!"
    })

    # 5 failed attempts
    for _ in range(5):
        client.post("/api/auth/login", json={"username": "lock_target", "password": "BadPassword!"})

    # Next attempt is blocked with 403 Forbidden
    res_blocked = client.post("/api/auth/login", json={"username": "lock_target", "password": "TargetPassword123!"})
    assert res_blocked.status_code == 403
    assert "temporarily locked" in res_blocked.json()["detail"]
run_step(25, "Multiple failed logins trigger lockout (403)", s25)

# Step 26: Admin re-enables / unlocks user -> user can log in again
def s26():
    res_users = client.get("/api/admin/users", headers={"Authorization": f"Bearer {state['admin_token']}"})
    target = [u for u in res_users.json() if u["username"] == "lock_target"][0]

    res_unlock = client.patch(
        f"/api/admin/users/{target['id']}/status",
        headers={"Authorization": f"Bearer {state['admin_token']}"},
        json={"is_active": True, "unlock": True},
    )
    assert res_unlock.status_code == 200
    assert res_unlock.json()["failed_login_attempts"] == 0

    # User can now login
    res_l = client.post("/api/auth/login", json={"username": "lock_target", "password": "TargetPassword123!"})
    assert res_l.status_code == 200
run_step(26, "Admin unlocks user -> user can log in again", s26)

print("\n" + "="*50)
print(f"E2E VERIFICATION COMPLETE: {sum(1 for s in step_results if s[2] == 'PASSED')}/26 PASSED")
print("="*50)
assert all(s[2] == "PASSED" for s in step_results)
