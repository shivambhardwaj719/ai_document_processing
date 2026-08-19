import json
import logging
from typing import Any


class StructuredLogger:
    def __init__(self, logger_name: str = "apps.documents"):
        self.logger = logging.getLogger(logger_name)

    def _log(self, level: int, event: str, extra_data: dict[str, Any]):
        log_entry = {
            "event": event,
            **extra_data,
        }
        self.logger.log(level, json.dumps(log_entry, default=str))

    def info(self, event: str, **kwargs):
        self._log(logging.INFO, event, kwargs)

    def warning(self, event: str, **kwargs):
        self._log(logging.WARNING, event, kwargs)

    def error(self, event: str, **kwargs):
        self._log(logging.ERROR, event, kwargs)

    def exception(self, event: str, **kwargs):
        self.logger.exception(json.dumps({"event": event, **kwargs}, default=str))


structured_logger = StructuredLogger()
