from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.audit_service import log_event

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Patients only)",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    """Register a new patient account with encrypted password and input validation."""
    # Prevent unauthorized privilege escalation
    if payload.role and payload.role.upper() != UserRole.PATIENT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public registration is restricted to PATIENT role only",
        )

    # Check for duplicate username or email
    existing_user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered",
        )

    # Hash password securely using bcrypt - plaintext password is never stored
    hashed_pwd = hash_password(payload.password)

    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed_pwd,
        role=UserRole.PATIENT,
        is_active=True,
    )
    db.add(new_user)
    db.flush()  # Flushes to obtain new_user.id for patient profile

    # Create associated Patient profile
    patient_profile = Patient(
        user_id=new_user.id,
        full_name=payload.full_name,
    )
    db.add(patient_profile)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verify credentials and issue signed JWT access token. Rejects invalid credentials safely."""
    # Lookup by username or email
    user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.username)
    ).first()

    now = datetime.now(timezone.utc)

    # Check if account is temporarily locked
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
                details=f"Login attempt rejected: Account '{user.username}' is locked until {user.locked_until}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is temporarily locked due to multiple failed login attempts. Please try again later.",
            )
        else:
            # Lockout expired, reset lockout state
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

    # Reject safely without leaking if username exists vs password wrong
    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                log_event(
                    db=db,
                    action="ACCOUNT_LOCKED",
                    resource_type="auth",
                    user_id=user.id,
                    details=f"Account '{user.username}' locked after {user.failed_login_attempts} failed login attempts",
                )
            db.commit()

        log_event(
            db=db,
            action="LOGIN_FAILURE",
            resource_type="auth",
            details=f"Failed login attempt for identifier: {payload.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive",
        )

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
        details=f"User '{user.username}' successfully signed in",
    )

    token = create_access_token(
        subject=user.id,
        claims={"username": user.username, "role": user.role.value},
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return currently authenticated user information. Sensitive fields like hashed_password are excluded."""
    return current_user
