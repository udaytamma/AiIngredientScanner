"""Structured logging configuration with daily rotating log files."""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from config.settings import get_settings


# Log directories
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
APP_LOG_DIR = LOG_DIR / "app"
SERVER_LOG_DIR = LOG_DIR / "server"


class StructuredFormatter(logging.Formatter):
    """JSON-like structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured output.

        Args:
            record: Log record to format.

        Returns:
            Formatted log string.
        """
        base = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            base.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        return str(base)


def _create_rotating_file_handler(
    log_dir: Path,
    filename_prefix: str,
    formatter: logging.Formatter,
) -> TimedRotatingFileHandler:
    """Create a daily rotating file handler.

    Args:
        log_dir: Directory for log files.
        filename_prefix: Prefix for log filenames.
        formatter: Log formatter to use.

    Returns:
        Configured TimedRotatingFileHandler.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{filename_prefix}.log"

    handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8",
    )
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(formatter)

    return handler


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure application logging with file and console output.

    Args:
        level: Optional log level override.

    Returns:
        Configured root logger.
    """
    settings = get_settings()
    log_level = level or settings.log_level

    formatter = StructuredFormatter()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Application log file handler (daily rotation)
    app_file_handler = _create_rotating_file_handler(
        APP_LOG_DIR, "app", formatter
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers = [console_handler, app_file_handler]

    return root_logger


def setup_server_logging(level: str | None = None) -> logging.Logger:
    """Configure server-specific logging with daily rotation.

    Args:
        level: Optional log level override.

    Returns:
        Configured server logger.
    """
    settings = get_settings()
    log_level = level or settings.log_level

    formatter = StructuredFormatter()

    # Server log file handler (daily rotation)
    server_file_handler = _create_rotating_file_handler(
        SERVER_LOG_DIR, "server", formatter
    )

    # Console handler for server logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Create dedicated server logger
    server_logger = logging.getLogger("server")
    server_logger.setLevel(getattr(logging, log_level.upper()))
    server_logger.handlers = [console_handler, server_file_handler]
    server_logger.propagate = False  # Don't duplicate to root logger

    return server_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Named logger instance.
    """
    return logging.getLogger(name)
