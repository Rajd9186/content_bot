import json
import logging
import sys
import uuid
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra") and record.extra:
            log_entry.update(record.extra)
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


_correlation_id: str | None = None


def set_correlation_id(cid: str | None = None) -> str:
    global _correlation_id
    _correlation_id = cid or str(uuid.uuid4())
    return _correlation_id


def get_correlation_id() -> str | None:
    return _correlation_id


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        cid = get_correlation_id()
        if cid and not hasattr(record, "correlation_id"):
            record.correlation_id = cid
        return True


_ROOT_CONFIGURED = False


def setup_logging(name: str = __name__) -> logging.Logger:
    global _ROOT_CONFIGURED

    if not _ROOT_CONFIGURED:
        _ROOT_CONFIGURED = True
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        handler.addFilter(CorrelationFilter())

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        # Remove default handlers to avoid duplication
        for h in root.handlers[:]:
            root.removeHandler(h)
        root.addHandler(handler)

    logger = logging.getLogger(name)
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
