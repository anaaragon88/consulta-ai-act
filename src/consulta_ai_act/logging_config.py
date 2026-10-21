"""Privacy-preserving logging configuration."""

from __future__ import annotations

import logging

SENSITIVE_LOG_FIELDS = frozenset(
    {"question", "prompt", "answer", "response", "api_key", "authorization", "secret"}
)


class SensitiveDataFilter(logging.Filter):
    """Drop structured records that contain values under sensitive field names."""

    def filter(self, record: logging.LogRecord) -> bool:
        for field_name in SENSITIVE_LOG_FIELDS:
            if field_name in record.__dict__:
                return False
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure standard-library logging without adding question content."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(handler)
    elif not any(isinstance(item, SensitiveDataFilter) for item in root_logger.filters):
        root_logger.addFilter(SensitiveDataFilter())