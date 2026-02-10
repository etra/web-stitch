"""Colored JSON logging for the stitch application."""
import json
import logging
import sys
from datetime import datetime, timezone


class ColoredJsonFormatter(logging.Formatter):
    """Logging formatter that outputs JSON lines wrapped in ANSI colors.

    JSON fields: timestamp (ISO 8601 UTC), level, message, module, function.
    Colors: DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red, CRITICAL=bold red.
    """

    COLOR_MAP = {
        logging.DEBUG: "\033[36m",      # cyan
        logging.INFO: "\033[32m",       # green
        logging.WARNING: "\033[33m",    # yellow
        logging.ERROR: "\033[31m",      # red
        logging.CRITICAL: "\033[1;31m", # bold red
    }
    RESET = "\033[0m"

    def format(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        line = json.dumps(entry)
        color = self.COLOR_MAP.get(record.levelno, "")
        return f"{color}{line}{self.RESET}"


def init_logging(app):
    """Configure app.logger and the 'stitch' parent logger with ColoredJsonFormatter.

    Reads LOG_LEVEL from app.config. Attaches a single StreamHandler to stdout.
    """
    level_name = app.config.get("LOG_LEVEL", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    formatter = ColoredJsonFormatter()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the 'stitch' parent logger so all stitch.* loggers inherit it
    stitch_logger = logging.getLogger("stitch")
    stitch_logger.setLevel(level)
    stitch_logger.handlers.clear()
    stitch_logger.addHandler(handler)

    # Configure Flask's app logger to use the same handler
    app.logger.setLevel(level)
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
