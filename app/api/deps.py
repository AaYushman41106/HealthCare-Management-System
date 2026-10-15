from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User, UserRole

# OAuth2 scheme extracts Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that extracts, validates JWT token from header or cookie, and returns the User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Support header first, then cookie
    active_token = token
    if not active_token and request:
        active_token = request.cookies.get("access_token")

    if not active_token:
        raise credentials_exception

    payload = decode_access_token(active_token)
    if not payload:
        raise credentials_exception

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise credentials_exception

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return user


def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional user dependency for public pages that adapt when logged in."""
    active_token = token
    if not active_token and request:
        active_token = request.cookies.get("access_token")

    if not active_token:
        return None

    payload = decode_access_token(active_token)
    if not payload:
        return None

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        return None

    try:
        user_id = int(user_id_raw)
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            return user
    except Exception:
        return None

    return None


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that verifies the current user has the ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required",
        )
    return current_user
