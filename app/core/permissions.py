import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from app.models.user import User, UserRole


def generate_csrf_token() -> str:
    """Generate a cryptographically secure random token for CSRF protection."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(request: Request, submitted_token: Optional[str]) -> bool:
    """Validate submitted CSRF token against the session cookie token."""
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token or not submitted_token:
        return False
    return secrets.compare_digest(cookie_token, submitted_token)


def check_is_admin(user: User) -> bool:
    """Return True if user has ADMIN role."""
    return user.role == UserRole.ADMIN


def check_is_doctor(user: User) -> bool:
    """Return True if user has DOCTOR role."""
    return user.role == UserRole.DOCTOR


def check_is_patient(user: User) -> bool:
    """Return True if user has PATIENT role."""
    return user.role == UserRole.PATIENT
