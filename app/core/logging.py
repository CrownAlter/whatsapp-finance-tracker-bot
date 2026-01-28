import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from logging.handlers import RotatingFileHandler


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/app.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_structured: bool = True
) -> logging.Logger:
    """Setup comprehensive logging with rotation and structured output."""
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_structured:
            console_formatter = StructuredFormatter()
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Always use structured format for files
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Set specific loggers to prevent propagation
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


# Setup default logging
logger = setup_logging()
