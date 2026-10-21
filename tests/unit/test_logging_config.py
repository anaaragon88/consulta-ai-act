"""Tests for privacy-preserving logging."""

import logging

from consulta_ai_act.logging_config import SensitiveDataFilter, configure_logging


def test_sensitive_structured_fields_are_dropped() -> None:
    record = logging.LogRecord(
        name="consulta_ai_act",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request processed",
        args=(),
        exc_info=None,
    )
    record.question = "confidential user question"

    assert SensitiveDataFilter().filter(record) is False


def test_safe_metadata_can_be_logged() -> None:
    record = logging.LogRecord(
        name="consulta_ai_act",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request processed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"

    assert SensitiveDataFilter().filter(record) is True


def test_configure_logging_sets_level() -> None:
    logger = logging.getLogger("consulta_ai_act.test")

    configure_logging("WARNING")

    assert logging.getLogger().level == logging.WARNING
    assert logger.isEnabledFor(logging.WARNING)
