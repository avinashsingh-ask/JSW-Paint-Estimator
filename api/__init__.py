"""API router initialization."""
from fastapi import APIRouter
from . import health, manual_estimation, cv_estimation

# Create main API router
api_router = APIRouter()

# Include routers
api_router.include_router(health.router)
api_router.include_router(manual_estimation.router)
api_router.include_router(cv_estimation.router)

__all__ = ['api_router']
