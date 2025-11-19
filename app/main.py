"""Stream Companion - Main FastAPI Application"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.core.config import settings, APP_NAME, APP_VERSION

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="OBS Web Overlay System with real-time control",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure media directory exists
media_path = Path(settings.media_directory)
media_path.mkdir(exist_ok=True)

# Mount static files for media assets
app.mount("/media", StaticFiles(directory=settings.media_directory), name="media")


@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": f"{APP_NAME} API",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
