import logging
import re
import sys
from typing import Optional

_SECRET_PATTERNS = [
    re.compile(r'(Authorization:\s*Bearer\s+)\S+', re.IGNORECASE),
    re.compile(r'(Authorization:\s*Basic\s+)\S+', re.IGNORECASE),
    re.compile(r'("api[_-]?key"\s*:\s*")[^"]+(")', re.IGNORECASE),
    re.compile(r'(api[_-]?key=)[^&\s]+', re.IGNORECASE),
    re.compile(r'("password"\s*:\s*")[^"]+(")', re.IGNORECASE),
    re.compile(r'("secret"\s*:\s*")[^"]+(")', re.IGNORECASE),
    re.compile(r'("token"\s*:\s*")[^"]+(")', re.IGNORECASE),
    re.compile(r'("bearer_token"\s*:\s*")[^"]+(")', re.IGNORECASE),
]


def _mask_secrets(message: str) -> str:
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub(lambda m: m.group(0)[:m.start(1) - m.start(0) + len(m.group(1))] + "***" + (m.group(2) if len(m.groups()) >= 2 else ""), message)
    return message


class _MaskingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return _mask_secrets(original)


def get_logger(name: str = "app", level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    from app.config.settings import get_settings
    effective_level = level or get_settings().log_level
    logger.setLevel(getattr(logging, effective_level, logging.INFO))

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_MaskingFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    return logger
