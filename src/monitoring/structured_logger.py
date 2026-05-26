"""
Structured JSON logger — Cloud Run emits these to Cloud Logging automatically.
Cloud Logging parses the `severity` and `message` fields natively; extra keys
become structured payload fields visible in Log Explorer.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class _StructuredFormatter(logging.Formatter):
    _SEVERITY = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    _SKIP = frozenset({
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "id", "levelname", "levelno", "lineno", "message",
        "module", "msecs", "msg", "name", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "thread", "threadName",
    })

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "severity": self._SEVERITY.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "logger": record.name,
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        for key, val in record.__dict__.items():
            if key not in self._SKIP:
                entry[key] = val
        return json.dumps(entry, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    """Replace root logger handlers with a single structured JSON handler."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_StructuredFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # Keep noisy third-party loggers quieter
    for name in ("httpx", "httpcore", "urllib3", "google.auth"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
