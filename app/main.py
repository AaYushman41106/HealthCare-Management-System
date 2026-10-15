from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables upon startup
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SecureCare - Adaptive SDLC Framework for Secure Development of a Healthcare Management System (Pure Python REST API Backend)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Safe CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount REST API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["System"])
def root_endpoint():
    """Root API endpoint providing platform information."""
    return {
        "message": "SecureCare Healthcare Management System REST API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "ui": "Streamlit Pure-Python UI running via `streamlit run streamlit_app.py`",
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Simple health check endpoint for monitoring."""
    return {"status": "healthy", "version": settings.VERSION}
