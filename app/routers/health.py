"""
Health and version endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from app import __version__, __author__, __contact__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AKSI Bot Backend",
    }


@router.get("/version")
async def version():
    """Version information endpoint"""
    return {
        "version": __version__,
        "service": "AKSI Bot Backend",
        "author": __author__,
        "contact": __contact__,
        "timestamp": datetime.utcnow().isoformat(),
    }
