"""Health check routes."""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from ....infrastructure.config import get_settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status information
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
    )


@router.get("/")
async def root():
    """Root endpoint.

    Returns:
        Welcome message
    """
    settings = get_settings()

    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
