"""Development Seeding Script for SecureCare (Sprint 2)

Seeds initial development/demo doctor accounts.
Idempotent: Running this multiple times will not create duplicate entries.
Note: These credentials are strictly for development and demonstration purposes.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import SessionLocal, init_db
from app.models.doctor import Doctor
from app.models.user import User, UserRole

DEV_DOCTORS = [
    {
        "username": "dr_priya",
        "email": "priya.sharma@securecare.org",
        "password": "DoctorSecure123!",
        "full_name": "Dr. Priya Sharma",
        "specialization": "Cardiology",
        "license_number": "DOC-CARD-1001",
        "phone": "+1-555-0101",
    },
    {
        "username": "dr_rahul",
        "email": "rahul.mehta@securecare.org",
        "password": "DoctorSecure123!",
        "full_name": "Dr. Rahul Mehta",
        "specialization": "General Medicine",
        "license_number": "DOC-GEN-1002",
        "phone": "+1-555-0102",
    },
]


def seed_doctors(db: Optional[Session] = None) -> int:
    """Idempotently seed development doctors into SQLite database.
    
    Returns the number of newly created doctor records.
    """
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    created_count = 0
    try:
        for doc_data in DEV_DOCTORS:
            # Check for existing user by username or email
            existing_user = (
                db.query(User)
                .filter(
                    (User.username == doc_data["username"])
                    | (User.email == doc_data["email"])
                )
                .first()
            )

            if existing_user:
                print(f"[SEED] Doctor '{doc_data['full_name']}' ({doc_data['username']}) already exists. Skipping.")
                continue

            # Create User record with DOCTOR role
            hashed_pwd = hash_password(doc_data["password"])
            user = User(
                username=doc_data["username"],
                email=doc_data["email"],
                hashed_password=hashed_pwd,
                role=UserRole.DOCTOR,
                is_active=True,
            )
            db.add(user)
            db.flush()

            # Create associated Doctor profile
            doctor = Doctor(
                user_id=user.id,
                full_name=doc_data["full_name"],
                specialization=doc_data["specialization"],
                license_number=doc_data["license_number"],
                phone=doc_data["phone"],
            )
            db.add(doctor)
            db.commit()
            created_count += 1
            print(f"[SEED] Successfully seeded '{doc_data['full_name']}' (Role: DOCTOR).")

        print(f"[SEED COMPLETED] Seeded {created_count} new doctors.")
        return created_count
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed doctors: {e}")
        raise
    finally:
        if should_close:
            db.close()
DEV_ADMIN = {
    "username": "admin",
    "email": "admin@securecare.org",
    "password": "AdminSecure123!",
}


def seed_admin(db: Optional[Session] = None) -> int:
    """Idempotently seed the default administrative user.
    
    Returns 1 if admin was newly created, 0 if already existed.
    """
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    try:
        existing_admin = (
            db.query(User)
            .filter(
                (User.username == DEV_ADMIN["username"])
                | (User.email == DEV_ADMIN["email"])
            )
            .first()
        )
        if existing_admin:
            print(f"[SEED] Admin user '{DEV_ADMIN['username']}' already exists. Skipping.")
            return 0

        hashed_pwd = hash_password(DEV_ADMIN["password"])
        admin_user = User(
            username=DEV_ADMIN["username"],
            email=DEV_ADMIN["email"],
            hashed_password=hashed_pwd,
            role=UserRole.ADMIN,
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
        )
        db.add(admin_user)
        db.commit()
        print(f"[SEED] Successfully seeded admin user '{DEV_ADMIN['username']}'.")
        return 1
    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed admin: {e}")
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed_doctors()
    seed_admin()
