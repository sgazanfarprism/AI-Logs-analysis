"""
Structured JSON Logger for Agentic Log Analysis System

This module provides a production-grade structured logging system
using Python's logging module with JSON formatting.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger with JSON output and context management
    
    Usage:
        logger = StructuredLogger("agent_name")
        logger.info("Processing started", extra={"count": 100})
        logger.error("Failed to process", extra={"error_code": "E001"})
    """
    
    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True
    ):
        """
        Initialize structured logger
        
        Args:
            name: Logger name (typically module or agent name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            console_output: Whether to output to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers = []  # Clear existing handlers
        
        formatter = JSONFormatter()
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Internal logging method"""
        log_record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level.upper()),
            "(unknown file)",
            0,
            message,
            (),
            None if not exc_info else sys.exc_info(),
            "(unknown function)"
        )
        
        if extra:
            log_record.extra_fields = extra
        
        self.logger.handle(log_record)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        self._log("DEBUG", message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        self._log("INFO", message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self._log("WARNING", message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message"""
        self._log("ERROR", message, extra, exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message"""
        self._log("CRITICAL", message, extra, exc_info)
    
    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log exception with traceback"""
        self._log("ERROR", message, extra, exc_info=True)


def get_logger(
    name: str,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> StructuredLogger:
    """
    Factory function to create a structured logger
    
    Args:
        name: Logger name
        log_level: Log level (defaults to INFO or environment variable)
        log_file: Log file path (defaults to logs/agentic_log_analysis.log)
    
    Returns:
        StructuredLogger instance
    """
    import os
    
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    if log_file is None:
        log_file = os.getenv("LOG_FILE", "logs/agentic_log_analysis.log")
    
    return StructuredLogger(name, log_level, log_file)


# Example usage
if __name__ == "__main__":
    # Test the logger
    logger = get_logger("test_logger", log_level="DEBUG")
    
    logger.debug("Debug message", extra={"debug_info": "test"})
    logger.info("Info message", extra={"count": 42})
    logger.warning("Warning message", extra={"threshold": 80})
    logger.error("Error message", extra={"error_code": "E001"})
    
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("Exception occurred", extra={"context": "test"})
