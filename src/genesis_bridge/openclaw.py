from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .config import BridgeConfig
from .ollama import ProviderError


class OpenClawClient:
    """Small, non-shell adapter for the documented `openclaw agent` command."""

    def __init__(self, config: BridgeConfig) -> None:
        self.config = config
        self.command = self._resolve_command(config.openclaw_command)

    @staticmethod
    def _resolve_command(command: str) -> str | None:
        path = Path(command).expanduser()
        if path.is_file():
            return str(path.resolve())
        return shutil.which(command)

    @property
    def available(self) -> bool:
        return self.command is not None

    def doctor(self) -> dict[str, Any]:
        if not self.command:
            return {"available": False, "command": self.config.openclaw_command}
        try:
            result = subprocess.run(
                [self.command, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
            return {
                "available": result.returncode == 0,
                "command": self.command,
                "version": (result.stdout or result.stderr).strip()[:300],
                "exit_code": result.returncode,
            }
        except (OSError, subprocess.SubprocessError) as exc:
            return {"available": False, "command": self.command, "error": str(exc)}

    def analyze(self, prompt_file: Path, cwd: Path | None = None) -> tuple[str, str, int]:
        if not self.command:
            raise ProviderError("OpenClaw wurde nicht gefunden.")
        command = [
            self.command,
            "agent",
            "--agent",
            self.config.openclaw_agent,
            "--message-file",
            str(prompt_file),
            "--json",
            "--timeout",
            str(self.config.openclaw_timeout_seconds),
        ]
        started = time.monotonic()
        env = os.environ.copy()
        # Prevent an accidental recursive bridge call when OpenClaw itself has this MCP server configured.
        env["GENESIS_BRIDGE_NESTED"] = "1"
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.openclaw_timeout_seconds + 15,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(f"OpenClaw Timeout nach {self.config.openclaw_timeout_seconds} Sekunden.") from exc
        except OSError as exc:
            raise ProviderError(f"OpenClaw konnte nicht gestartet werden: {exc}") from exc
        duration_ms = int((time.monotonic() - started) * 1000)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ProviderError(f"OpenClaw Exit-Code {result.returncode}: {detail[:800]}")
        text = extract_text(result.stdout)
        if not text:
            raise ProviderError("OpenClaw hat eine leere Antwort geliefert.")
        return text, self.config.openclaw_agent, duration_ms


def extract_text(output: str) -> str:
    value = output.strip()
    if not value:
        return ""
    candidates: list[Any] = []
    try:
        candidates.append(json.loads(value))
    except json.JSONDecodeError:
        for line in reversed(value.splitlines()):
            try:
                candidates.append(json.loads(line))
                break
            except json.JSONDecodeError:
                continue
    for candidate in candidates:
        found = _find_text(candidate)
        if found:
            return found.strip()
    return value


def _find_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for item in reversed(value):
            found = _find_text(item)
            if found:
                return found
        return None
    if isinstance(value, dict):
        for key in ("reply", "text", "content", "message", "output", "result"):
            if key in value:
                found = _find_text(value[key])
                if found:
                    return found
    return None
