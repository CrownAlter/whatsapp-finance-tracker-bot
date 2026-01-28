from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import get_logger
import time

logger = get_logger(__name__)

# Enable SQLAlchemy logging
engine = create_engine(
    settings.create_database_url,
    echo=False,  # We'll handle logging ourselves
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log before database query execution."""
    context._query_start_time = time.time()
    
    # Log query details (without sensitive data)
    logger.debug(
        "Database query started",
        extra={
            "event_type": "db_query_start",
            "statement": statement[:200] + "..." if len(statement) > 200 else statement,
            "executemany": executemany,
            "parameters_count": len(parameters) if parameters else 0
        }
    )


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log after database query execution."""
    total = time.time() - context._query_start_time
    
    logger.debug(
        "Database query completed",
        extra={
            "event_type": "db_query_complete",
            "statement": statement[:200] + "..." if len(statement) > 200 else statement,
            "duration_seconds": total,
            "executemany": executemany,
            "rowcount": cursor.rowcount if hasattr(cursor, 'rowcount') else None
        }
    )


@event.listens_for(engine, "handle_error")
def handle_error(exception, context):
    """Log database errors."""
    logger.error(
        f"Database error: {type(exception).__name__}: {str(exception)}",
        extra={
            "event_type": "db_error",
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "statement": context.statement[:200] + "..." if len(context.statement) > 200 else context.statement,
            "parameters": str(context.parameters)[:100] if context.parameters else None
        }
    )


def get_db():
    """Database session dependency with error handling and logging."""
    db = SessionLocal()
    request_id = getattr(db, 'request_id', None)
    
    try:
        logger.debug(
            "Database session opened",
            extra={
                "event_type": "db_session_start",
                "request_id": request_id
            }
        )
        yield db
    except Exception as e:
        logger.error(
            f"Database session error: {type(e).__name__}: {str(e)}",
            extra={
                "event_type": "db_session_error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "request_id": request_id
            }
        )
        db.rollback()
        raise
    finally:
        try:
            db.close()
            logger.debug(
                "Database session closed",
                extra={
                    "event_type": "db_session_end",
                    "request_id": request_id
                }
            )
        except Exception as e:
            logger.error(
                f"Error closing database session: {type(e).__name__}: {str(e)}",
                extra={
                    "event_type": "db_session_close_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "request_id": request_id
                }
            )


def get_db_with_logging(request_id: str = None):
    """Database session dependency with request ID tracking."""
    db = SessionLocal()
    db.request_id = request_id
    
    try:
        logger.info(
            "Database session with request ID opened",
            extra={
                "event_type": "db_session_start_with_id",
                "request_id": request_id
            }
        )
        yield db
    except Exception as e:
        logger.error(
            f"Database session error (ID: {request_id}): {type(e).__name__}: {str(e)}",
            extra={
                "event_type": "db_session_error_with_id",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "request_id": request_id
            }
        )
        db.rollback()
        raise
    finally:
        try:
            db.close()
            logger.info(
                "Database session with request ID closed",
                extra={
                    "event_type": "db_session_end_with_id",
                    "request_id": request_id
                }
            )
        except Exception as e:
            logger.error(
                f"Error closing database session (ID: {request_id}): {type(e).__name__}: {str(e)}",
                extra={
                    "event_type": "db_session_close_error_with_id",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "request_id": request_id
                }
            )
