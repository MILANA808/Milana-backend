"""
Milana-backend (AKSI) - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import os

from app.routers import health, aksi, echo

app = FastAPI(
    title="AKSI Bot Backend",
    description="FastAPI backend for AKSI / Milana services",
    version="1.0.0",
    contact={
        "name": "Alfiia Bashirova (AKSI Project)",
        "email": "716elektrik@mail.ru",
    },
)

# Include routers
app.include_router(health.router)
app.include_router(aksi.router, prefix="/aksi", tags=["aksi"])
app.include_router(echo.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AKSI Bot Backend API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "echo": "/echo",
            "aksi_metrics": "/aksi/metrics",
            "aksi_proof": "/aksi/proof",
            "aksi_logs": "/aksi/logs",
        },
        "documentation": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": str(request.url),
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
