import logging
from datetime import datetime, timezone
from functools import wraps
from time import perf_counter

logger = logging.getLogger(__name__)


def camelcase(s):
    parts = iter(s.split('_'))
    return next(parts) + ''.join(i.title() for i in parts)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def log_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        started_at = perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.info(f'{func.__qualname__} executed', extra={'duration_ms': elapsed_ms})
        return result

    return wrapper
