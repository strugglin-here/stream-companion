"""Stream Companion - Main FastAPI Application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.core.config import settings, APP_NAME, APP_VERSION
from app.core.database import init_db, close_db
from app.api import elements, websocket, media


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Runs on application startup:
    - Initialize database (create tables if they don't exist)
    - Create media directory if needed
    
    Runs on application shutdown:
    - Close database connections
    """
    # Startup
    await init_db()
    print(f"✓ Database initialized")
    
    # Ensure media directory exists
    media_path = Path(settings.media_directory)
    media_path.mkdir(exist_ok=True)
    print(f"✓ Media directory ready: {settings.media_directory}")
    
    yield
    
    # Shutdown
    await close_db()
    print(f"✓ Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="Web Overlay System with real-time control",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(elements.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(websocket.router)  # WebSocket at /ws

# Mount static files for HTML pages and assets
# Note: StaticFiles must be mounted AFTER API routers to avoid route conflicts
app.mount("/media", StaticFiles(directory=settings.media_directory, html=True), name="media")


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
        reload=settings.debug,
        reload_dirs=["app", "data"] if settings.debug else None
    )
