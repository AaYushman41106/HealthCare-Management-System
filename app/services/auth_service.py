from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.services.audit_service import log_event


class AuthService:
    """Authentication and Account Security Service."""

    @staticmethod
    def authenticate_user(
        db: Session,
        username_or_email: str,
        password: str,
        client_ip: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Verify credentials and enforce brute-force lockout defense.
        Returns (user, None) on success, or (None, error_message) on failure.
        """
        now = datetime.now(timezone.utc)
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        # Check account lockout
        if user and user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > now:
                log_event(
                    db=db,
                    action="LOGIN_LOCKED",
                    resource_type="auth",
                    user_id=user.id,
                    ip_address=client_ip,
                    details=f"Login attempt rejected: Account '{user.username}' is locked until {user.locked_until}",
                )
                return None, "Account is temporarily locked due to multiple failed login attempts. Please try again later or contact an administrator."
            else:
                # Lockout expired
                user.failed_login_attempts = 0
                user.locked_until = None
                db.commit()

        # Check password verification safely
        if not user or not verify_password(password, user.hashed_password):
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                    log_event(
                        db=db,
                        action="ACCOUNT_LOCKED",
                        resource_type="auth",
                        user_id=user.id,
                        ip_address=client_ip,
                        details=f"Account '{user.username}' locked after {user.failed_login_attempts} failed login attempts",
                    )
                db.commit()

            log_event(
                db=db,
                action="LOGIN_FAILURE",
                resource_type="auth",
                ip_address=client_ip,
                details=f"Failed login attempt for identifier: {username_or_email}",
            )
            return None, "Invalid username or password"

        if not user.is_active:
            return None, "Account is inactive. Please contact an administrator."

        # Reset failed attempts upon successful login
        if (user.failed_login_attempts or 0) > 0 or user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

        log_event(
            db=db,
            action="LOGIN_SUCCESS",
            resource_type="auth",
            user_id=user.id,
            ip_address=client_ip,
            details=f"User '{user.username}' successfully signed in",
        )

        return user, None

    @staticmethod
    def register_patient(
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new patient account with encrypted password and patient profile.
        Returns (new_user, None) or (None, error_message).
        """
        # Check duplicate
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return None, "Username or email is already registered."

        hashed_pwd = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_pwd,
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        parsed_dob = None
        if date_of_birth:
            try:
                from datetime import date as dt_date
                parsed_dob = dt_date.fromisoformat(date_of_birth) if isinstance(date_of_birth, str) else date_of_birth
            except Exception:
                parsed_dob = None

        patient_profile = Patient(
            user_id=new_user.id,
            full_name=full_name,
            phone=phone,
            date_of_birth=parsed_dob,
            gender=gender,
            address=address,
        )
        db.add(patient_profile)
        db.commit()
        db.refresh(new_user)

        log_event(
            db=db,
            action="USER_REGISTERED",
            resource_type="user",
            user_id=new_user.id,
            ip_address=client_ip,
            details=f"Patient '{username}' self-registered",
        )

        return new_user, None

    @staticmethod
    def create_user_token(user: User) -> str:
        """Create signed JWT access token for user."""
        return create_access_token(
            subject=user.id,
            claims={"username": user.username, "role": user.role.value},
        )
