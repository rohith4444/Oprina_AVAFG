"""
Enhanced logging setup for Oprina API.

This module provides centralized logging configuration with support for:
- Different log levels for development vs production
- Structured logging with JSON format
- Request ID tracking
- Performance monitoring
"""

import logging
import logging.config
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

class RequestIDFilter(logging.Filter):
    """Filter to add request ID to log records."""
    
    def filter(self, record):
        # Add request ID if not present
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(self, '_request_id', 'no-request')
        return True
    
    def set_request_id(self, request_id: str):
        """Set the current request ID."""
        self._request_id = request_id


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message',
                          'request_id']:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


def setup_logger(
    name: str = "oprina-api",
    level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True,
    log_dir: Optional[Path] = None,
    json_format: bool = False
) -> logging.Logger:
    """
    Set up a logger with the specified configuration.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output to console
        file_output: Whether to output to file
        log_dir: Directory for log files
        json_format: Whether to use JSON formatting
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
        )
    
    # Create request ID filter
    request_filter = RequestIDFilter()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(request_filter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        if log_dir is None:
            log_dir = Path("logs")
        
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"{name}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(request_filter)
        logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(
            log_dir / f"{name}_errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(request_filter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str = "oprina-api") -> logging.Logger:
    """Get an existing logger or create a new one with default settings."""
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


def setup_production_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """Set up logging for production environment."""
    return setup_logger(
        name="oprina-api",
        level="WARNING",
        console_output=False,
        file_output=True,
        log_dir=log_dir,
        json_format=True
    )


def setup_development_logging() -> logging.Logger:
    """Set up logging for development environment."""
    return setup_logger(
        name="oprina-api",
        level="DEBUG",
        console_output=True,
        file_output=True,
        json_format=False
    )


def log_function_call(logger: logging.Logger):
    """Decorator to log function calls with arguments and return values."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    'function': func.__name__,
                    'args': str(args)[:200],  # Limit length
                    'kwargs': str(kwargs)[:200]
                }
            )
            
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Function {func.__name__} completed successfully",
                    extra={'function': func.__name__}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed: {str(e)}",
                    extra={
                        'function': func.__name__,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_performance(logger: logging.Logger):
    """Decorator to log function performance metrics."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Performance: {func.__name__} completed in {duration:.3f}s",
                    extra={
                        'function': func.__name__,
                        'duration_seconds': duration,
                        'performance': True
                    }
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance: {func.__name__} failed after {duration:.3f}s",
                    extra={
                        'function': func.__name__,
                        'duration_seconds': duration,
                        'error': str(e),
                        'performance': True
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator
