"""Structured engineering logger for WindCtrl Validate."""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "windctrl",
    log_level: str = "INFO",
    run_id: Optional[str] = None,
) -> logging.Logger:
    """Configure a structured stream logger with engineering metadata formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers on re-initialization
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        format_str = (
            "[%(asctime)s] [%(levelname)s] [WindCtrl"
            + (f":{run_id}" if run_id else "")
            + "] [%(name)s] %(message)s"
        )
        formatter = logging.Formatter(fmt=format_str, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()
