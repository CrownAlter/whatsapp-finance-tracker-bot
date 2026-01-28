from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import psutil
import time
from datetime import datetime, timedelta
from sqlalchemy import text
from app.db.session import get_db
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float
    system: Dict[str, Any]
    database: Optional[Dict[str, Any]] = None
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response model."""
    timestamp: datetime
    uptime_seconds: float
    requests: Dict[str, Any]
    system: Dict[str, Any]
    database: Optional[Dict[str, Any]] = None


# Global metrics storage
class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.request_times = []
        self.error_count = 0
        self.endpoint_stats = {}
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record request metrics."""
        self.request_count += 1
        self.request_times.append(duration)
        
        # Keep only last 1000 request times for percentile calculation
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        if status_code >= 400:
            self.error_count += 1
        
        endpoint_key = f"{method} {path}"
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                "count": 0,
                "total_time": 0,
                "errors": 0
            }
        
        self.endpoint_stats[endpoint_key]["count"] += 1
        self.endpoint_stats[endpoint_key]["total_time"] += duration
        if status_code >= 400:
            self.endpoint_stats[endpoint_key]["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = time.time() - self.start_time
        avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        
        # Calculate percentiles
        sorted_times = sorted(self.request_times)
        n = len(sorted_times)
        p50 = sorted_times[int(n * 0.5)] if n > 0 else 0
        p95 = sorted_times[int(n * 0.95)] if n > 0 else 0
        p99 = sorted_times[int(n * 0.99)] if n > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "uptime_seconds": uptime,
            "avg_response_time": avg_response_time,
            "response_time_p50": p50,
            "response_time_p95": p95,
            "response_time_p99": p99,
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0,
            "endpoint_stats": self.endpoint_stats
        }


metrics = MetricsCollector()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Comprehensive health check endpoint."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
        
        # Database health check
        db_info = None
        try:
            db = next(get_db())
            result = db.execute(text("SELECT 1 as health_check"))
            db_info = {
                "status": "healthy",
                "connection_test": "passed"
            }
            db.close()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_info = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Services health
        services = {
            "database": db_info["status"] if db_info else "unknown",
            "logging": "healthy",
            "metrics": "healthy"
        }
        
        overall_status = "healthy"
        if db_info and db_info["status"] != "healthy":
            overall_status = "degraded"
        if cpu_percent > 90 or memory.percent > 90:
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - metrics.start_time,
            system=system_info,
            database=db_info,
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - metrics.start_time,
            system={"error": str(e)},
            services={"status": "unhealthy"}
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get application metrics."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "process_count": len(psutil.pids())
        }
        
        # Database metrics
        db_info = None
        try:
            db = next(get_db())
            # Get basic DB stats
            result = db.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """))
            db_stats = result.fetchone()
            
            db_info = {
                "total_connections": db_stats.total_connections if db_stats else 0,
                "active_connections": db_stats.active_connections if db_stats else 0,
                "status": "healthy"
            }
            db.close()
        except Exception as e:
            logger.error(f"Database metrics failed: {e}")
            db_info = {"status": "error", "error": str(e)}
        
        app_metrics = metrics.get_metrics()
        
        return MetricsResponse(
            timestamp=datetime.utcnow(),
            uptime_seconds=app_metrics["uptime_seconds"],
            requests=app_metrics,
            system=system_info,
            database=db_info
        )
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise


@router.post("/metrics/reset")
async def reset_metrics():
    """Reset application metrics."""
    global metrics
    metrics = MetricsCollector()
    logger.info("Application metrics reset")
    return {"status": "metrics reset"}


def get_metrics_collector():
    """Get the global metrics collector instance."""
    return metrics