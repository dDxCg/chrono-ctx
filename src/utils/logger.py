import logging
from functools import wraps
from typing import Callable

def setup_logger(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

def get_logger(name: str):
    return logging.getLogger(name)

def log_enabled(description: str | None = None):
    def decorator(func: Callable):
        logger = get_logger(func.__module__)
        name = (
            f"{func.__qualname__} ({description})"
            if description
            else func.__qualname__
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                logger.info(
                    f"[SUCCEEDED] {name}"
                )
                return res
            except Exception:
                logger.exception(
                    f"[FAILED] {name}"
                )
                raise

        return wrapper
    
    if callable(description):
        return decorator(description)

    return decorator  