#!/usr/bin/env python3
"""Stable launcher for Claude Desktop/OpenClaw MCP and the local UI."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from genesis_bridge.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
