from fastapi import FastAPI, Request
from app.api.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import ErrorHandlerMiddleware, RequestLoggingMiddleware
from app.core.monitoring import router as monitoring_router, get_metrics_collector
from app.db.base import Base
from app.db.session import engine
from twilio.twiml.messaging_response import MessagingResponse
import atexit
import time

# Setup comprehensive logging first
logger = setup_logging(
    log_level=getattr(settings, 'LOG_LEVEL', 'INFO'),
    log_file=getattr(settings, 'LOG_FILE', 'logs/app.log'),
    enable_console=True,
    enable_structured=True
)

app_logger = get_logger(__name__)

# Create tables on startup (for simple apps/dev)
# In production, use Alembic migrations
try:
    Base.metadata.create_all(bind=engine)
    app_logger.info("Database tables created/verified successfully")
except Exception as e:
    app_logger.error(f"Database table creation failed: {type(e).__name__}: {str(e)}")
    raise

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="WhatsApp Finance Tracker Bot with comprehensive monitoring and logging",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware in the correct order
app.add_middleware(
    ErrorHandlerMiddleware
)

app.add_middleware(
    RequestLoggingMiddleware,
    log_body=getattr(settings, 'LOG_REQUEST_BODY', False),
    max_body_size=getattr(settings, 'MAX_LOG_BODY_SIZE', 1000)
)

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

# Metrics middleware integration
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect metrics for all requests."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", "unknown")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Record metrics (exclude monitoring endpoints to avoid noise)
        if not str(request.url.path).startswith("/monitoring"):
            metrics = get_metrics_collector()
            metrics.record_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration=process_time
            )
        
        return response
    
    except Exception as e:
        process_time = time.time() - start_time
        
        # Record error metrics
        if not str(request.url.path).startswith("/monitoring"):
            metrics = get_metrics_collector()
            metrics.record_request(
                method=request.method,
                path=str(request.url.path),
                status_code=500,
                duration=process_time
            )
        
        raise

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    app_logger.info(
        "Finance Tracker Bot starting up",
        extra={
            "event_type": "app_startup",
            "app_name": settings.PROJECT_NAME,
            "environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "api_version": "2.0.0"
        }
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    app_logger.info(
        "Finance Tracker Bot shutting down",
        extra={
            "event_type": "app_shutdown",
            "app_name": settings.PROJECT_NAME,
            "uptime_seconds": time.time() - get_metrics_collector().start_time
        }
    )

@app.get("/")
async def root():
    """Root endpoint with basic information."""
    metrics = get_metrics_collector()
    uptime = time.time() - metrics.start_time
    
    return {
        "message": "Finance Tracker Bot API",
        "version": "2.0.0",
        "status": "running",
        "uptime_seconds": uptime,
        "endpoints": {
            "api_docs": "/docs",
            "health": "/monitoring/health",
            "metrics": "/monitoring/metrics",
            "webhook": "/api/v1/webhook"
        }
    }

# Legacy webhook endpoint (redirects to new location)
@app.post("/webhook")
async def legacy_webhook(request: Request):
    """Legacy webhook endpoint - redirects to new endpoint."""
    app_logger.warning(
        "Legacy webhook endpoint called - should use /api/v1/webhook",
        extra={
            "event_type": "legacy_endpoint_used",
            "path": "/webhook",
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Forward to the new webhook endpoint
    from app.api.v1.endpoints.webhook import whatsapp_webhook
    return await whatsapp_webhook(request)

# Cleanup function to be called on exit
def cleanup():
    """Cleanup function called on application exit."""
    app_logger.info("Application cleanup completed")

# Register cleanup function
atexit.register(cleanup)

# Log application ready state
app_logger.info(
    "Finance Tracker Bot application initialized successfully",
    extra={
        "event_type": "app_ready",
        "project_name": settings.PROJECT_NAME,
        "api_v1_prefix": settings.API_V1_STR
    }
)