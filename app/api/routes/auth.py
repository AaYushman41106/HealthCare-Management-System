from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
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

    # Reject safely without leaking if username exists vs password wrong
    if not user or not verify_password(payload.password, user.hashed_password):
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
