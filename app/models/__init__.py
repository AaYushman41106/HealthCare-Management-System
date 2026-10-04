# app/models/__init__.py
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor

__all__ = ["User", "UserRole", "Patient", "Doctor"]
