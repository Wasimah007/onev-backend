"""
FastAPI application main module.
"""

import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.db import connect_db, disconnect_db
from app.routers.users import router as users_router
from app.auth.router import router as auth_router
from app.routers.syn_from_onev import router as sync_from_onev_router
# from app.routers.timesheets import router as timesheet_router
# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up FastAPI application")
    try:
        await connect_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application")
    try:
        await disconnect_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error("Error during database disconnect", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Production-ready FastAPI backend with raw SQL and JWT authentication",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler for proper error logging."""
    logger.warning(
        "HTTP exception",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version
    }


# Include routers
app.include_router(auth_router, prefix=settings.api_v1_prefix)
# app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(sync_from_onev_router, prefix=settings.api_v1_prefix)
# app.include_router(users_router, prefix=settings.api_v1_prefix)
# app.include_router(timesheet_router, prefix=settings.api_v1_prefix)
# app.include_router(projects_router, prefix=settings.api_v1_prefix)
#app.include_router(organisation_router, prefix=settings.api_v1_prefix)
# app.include_router(manager_router, prefix=settings.api_v1_prefix)
# app.include_router(user_sync_router, prefix=settings.api_v1_prefix)
# app.include_router(auth_router, prefix=settings.api_v1_prefix)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )