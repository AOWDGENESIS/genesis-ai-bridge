from __future__ import annotations

import logging
import os
from pathlib import Path


def configure_logging(data_dir: Path, verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("genesis_bridge")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    # MCP stdout is a protocol channel; logs must never be written there.
    stream = logging.StreamHandler()
    stream.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(stream)
    try:
        log_dir = data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "bridge.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(file_handler)
    except OSError:
        # A diagnostic tool must remain usable if the optional log file cannot be opened.
        pass
    logger.propagate = False
    return logger
