# app/api/routes/__init__.py
from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.doctors import router as doctors_router
from app.api.routes.appointments import router as appointments_router
from app.api.routes.medical_records import router as medical_records_router
from app.api.routes.admin import router as admin_router
from app.api.routes.integrations import router as integrations_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(doctors_router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(appointments_router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(medical_records_router, prefix="/medical-records", tags=["Medical Records"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])

