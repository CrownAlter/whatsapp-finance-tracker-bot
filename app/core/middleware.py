from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import traceback
import uuid
from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling and logging."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state for use in endpoints
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
        except HTTPException as http_exc:
            return await self._handle_http_exception(request, http_exc, request_id)
        except Exception as exc:
            return await self._handle_generic_exception(request, exc, request_id)
    
    async def _handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException, 
        request_id: str
    ) -> JSONResponse:
        """Handle HTTP exceptions with proper logging."""
        
        error_data = {
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": request_id
            },
            "request": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client": request.client.host if request.client else None
            }
        }
        
        logger.error(
            f"HTTP Exception: {exc.status_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "error_type": "HTTPException",
                "error_detail": exc.detail,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_data
        )
    
    async def _handle_generic_exception(
        self, 
        request: Request, 
        exc: Exception, 
        request_id: str
    ) -> JSONResponse:
        """Handle generic exceptions with comprehensive logging."""
        
        error_traceback = traceback.format_exc()
        
        error_data = {
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "request_id": request_id,
                "timestamp": traceback.extract_tb(exc.__traceback__)[-1].lineno if exc.__traceback__ else None
            },
            "request": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client": request.client.host if request.client else None
            }
        }
        
        logger.critical(
            f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "request_id": request_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": error_traceback,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=error_data
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    def __init__(self, app: ASGIApp, log_body: bool = False, max_body_size: int = 1000):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        # Log request
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": request_id
        }
        
        # Log request body if enabled and it's not too large
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    request_data["body"] = body.decode("utf-8", errors="ignore")
                else:
                    request_data["body"] = f"<body too large: {len(body)} bytes>"
            except Exception:
                request_data["body"] = "<unable to read body>"
        
        logger.info(
            f"Request: {request.method} {request.url}",
            extra={
                "event_type": "request_start",
                "request_id": request_id,
                **request_data
            }
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "process_time": round(process_time, 4),
                "request_id": request_id
            }
            
            log_level = logging.ERROR if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"Response: {response.status_code} - {process_time:.4f}s",
                extra={
                    "event_type": "request_end",
                    "request_id": request_id,
                    **response_data
                }
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed after {process_time:.4f}s: {type(exc).__name__} - {str(exc)}",
                extra={
                    "event_type": "request_failed",
                    "request_id": request_id,
                    "process_time": process_time,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)
                }
            )
            raise


# Import time for request timing
import time
import logging