"""Logging setup: every line carries a context id (request id in the API, job id in the worker).
Only ids, statuses and timings are logged — never field values or file contents."""

import contextvars
import logging

context_id: contextvars.ContextVar[str] = contextvars.ContextVar("context_id", default="-")


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.ctx = context_id.get()
        return True


def setup() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s [%(ctx)s] %(message)s")
    for handler in logging.getLogger().handlers:
        handler.addFilter(_ContextFilter())
