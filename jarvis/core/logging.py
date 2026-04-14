"""
JARVIS AI Agent - Comprehensive Logging System

Provides centralized logging for all agent operations, decisions, and events.
Logs to both console and file with structured format.
"""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger as loguru_logger
from typing import Optional

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Remove default handler
loguru_logger.remove()

# Log format with colors
LOG_FORMAT = (
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Add console handler
loguru_logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="DEBUG",
    colorize=True,
)

# Add file handler (rotating logs)
loguru_logger.add(
    LOGS_DIR / "jarvis-{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="500 MB",
    retention="7 days",
    colorize=False,
)

# Add detailed file handler for critical events
loguru_logger.add(
    LOGS_DIR / "jarvis-critical-{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="500 MB",
    retention="30 days",
    colorize=False,
)


class Logger:
    """Wrapper around loguru for consistent logging across JARVIS."""

    def __init__(self, name: str):
        """
        Initialize logger for a module.
        
        Args:
            name: Module name (usually __name__)
        """
        self.logger = loguru_logger.bind(module=name)
        self.name = name

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)

    def success(self, message: str, **kwargs):
        """Log success message."""
        self.logger.success(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def log_action(self, action: str, details: Optional[dict] = None):
        """
        Log an action taken by the agent.
        
        Args:
            action: Action name (e.g., "code_execution", "web_search")
            details: Additional context (dict)
        """
        msg = f"[ACTION] {action}"
        if details:
            msg += f" | {details}"
        self.logger.info(msg)

    def log_decision(self, decision: str, reasoning: str, options: Optional[list] = None):
        """
        Log a decision made by the agent.
        
        Args:
            decision: What was decided
            reasoning: Why this decision was made
            options: Alternative options considered
        """
        msg = f"[DECISION] {decision} | REASONING: {reasoning}"
        if options:
            msg += f" | OPTIONS: {options}"
        self.logger.info(msg)

    def log_error(self, error_type: str, message: str, recovery: Optional[str] = None):
        """
        Log an error with context.
        
        Args:
            error_type: Type of error
            message: Error message
            recovery: Recovery strategy if applicable
        """
        msg = f"[ERROR] {error_type}: {message}"
        if recovery:
            msg += f" | RECOVERY: {recovery}"
        self.logger.error(msg)

    def log_performance(self, operation: str, duration_ms: float, success: bool, details: Optional[dict] = None):
        """
        Log performance metrics for an operation.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            details: Additional metrics
        """
        status = "✓" if success else "✗"
        msg = f"[PERF] {status} {operation} | {duration_ms:.2f}ms"
        if details:
            msg += f" | {details}"
        level = "success" if success else "warning"
        self.logger.log(level, msg)


def get_logger(name: str) -> Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return Logger(name)
