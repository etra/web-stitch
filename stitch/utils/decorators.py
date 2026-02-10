"""Shared route decorators for the stitch application."""
import functools
import logging

from flask import request

logger = logging.getLogger(__name__)


def deprecated(reason=""):
    """Mark a route as deprecated.

    Logs a CRITICAL message on every request with endpoint, method, path,
    remote_addr, and reason. The original function still executes (non-breaking).
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            logger.critical(
                "Deprecated route accessed: endpoint=%s method=%s path=%s remote_addr=%s reason=%s",
                request.endpoint,
                request.method,
                request.path,
                request.remote_addr,
                reason,
            )
            return f(*args, **kwargs)
        return wrapper
    return decorator
