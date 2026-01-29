# src/logging_config.py
"""Centralized logging configuration for the P&C CPI pipeline."""

import logging
import os
from pathlib import Path

def setup_logging(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging with console and file handlers.

    Args:
        name: Logger name (typically __name__ from calling module)
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Create logs directory relative to project root
    script_dir = Path(__file__).parent
    logs_dir = script_dir.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = logging.FileHandler(logs_dir / "pipeline.log")
    file_handler.setLevel(log_level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
