import logging
import re
import sys
from typing import Any, Dict
from app.config.settings import settings

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"), # JWT regex
]

class SecretMaskingFilter(logging.Filter):
    """Filters log records to prevent leaking secrets, tokens, and passwords."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.mask_secrets(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.mask_secrets(str(v)) for v in record.args)
        return True

    @staticmethod
    def mask_secrets(text: str) -> str:
        masked = text
        for pat in SECRET_PATTERNS:
            def repl(m: re.Match) -> str:
                if len(m.groups()) == 2:
                    return f"{m.group(1)}=[REDACTED]"
                return "[REDACTED_TOKEN]"
            masked = pat.sub(repl, masked)
        return masked


def get_logger(name: str = "multimind") -> logging.Logger:
    """Returns a configured logger with standard formatting, file output, and secret filtering."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        level_str = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level_str)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        mask_filter = SecretMaskingFilter()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(mask_filter)
        logger.addHandler(console_handler)

        # File handler
        try:
            file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.addFilter(mask_filter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # Fall back to console only if file not writable

        logger.propagate = False

    return logger
