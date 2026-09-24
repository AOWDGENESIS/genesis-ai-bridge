from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import BridgeConfig, project_root
from .paths import atomic_write_json, expand_path


SERVER_NAME = "genesis-ai-bridge"


def claude_desktop_config_path() -> Path:
    override = os.environ.get("CLAUDE_DESKTOP_CONFIG")
    if override:
        return expand_path(override)
    appdata = os.environ.get("APPDATA")
    if appdata:
        return expand_path(Path(appdata) / "Claude" / "claude_desktop_config.json")
    return expand_path(Path.home() / ".config" / "Claude" / "claude_desktop_config.json")


def openclaw_config_path() -> Path:
    override = os.environ.get("OPENCLAW_CONFIG_PATH")
    if override:
        return expand_path(override)
    return expand_path(Path.home() / ".openclaw" / "openclaw.json")


def _backup(path: Path, keep: int = 3) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = path.with_name(f"{path.name}.genesis-backup-{stamp}")
    shutil.copy2(path, destination)
    backups = sorted(path.parent.glob(f"{path.name}.genesis-backup-*"), key=lambda item: item.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old.unlink(missing_ok=True)
    return destination


def _launcher_path() -> Path:
    return project_root() / "scripts" / "genesis-bridge.py"


def claude_entry(config: BridgeConfig) -> dict[str, Any]:
    launcher = _launcher_path()
    return {
        "command": sys.executable,
        "args": [str(launcher), "mcp"],
        "env": {
            "PYTHONUTF8": "1",
            "GENESIS_BRIDGE_CONFIG": str(config.config_path or ""),
            "GENESIS_BRIDGE_ROOT": str(project_root()),
        },
    }


def install_claude_mcp(config: BridgeConfig, path: Path | None = None) -> dict[str, Any]:
    target = path or claude_desktop_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup(target)
    if target.exists():
        try:
            with target.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Claude-Konfiguration ist kein gültiges JSON; sie wurde nicht verändert: {exc}") from exc
    else:
        document = {}
    if not isinstance(document, dict):
        raise ValueError("Claude-Konfiguration muss ein JSON-Objekt sein.")
    servers = document.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcpServers in der Claude-Konfiguration muss ein Objekt sein.")
    servers[SERVER_NAME] = claude_entry(config)
    atomic_write_json(target, document)
    return {"path": str(target), "backup": str(backup) if backup else None, "server": SERVER_NAME}


def openclaw_command() -> str | None:
    return shutil.which("openclaw")


def openclaw_add_mcp(config: BridgeConfig) -> dict[str, Any]:
    command = openclaw_command()
    launcher = _launcher_path()
    args = [
        command or "openclaw",
        "mcp",
        "add",
        SERVER_NAME,
        "--command",
        sys.executable,
        "--arg",
        str(launcher),
        "--arg",
        "mcp",
        "--cwd",
        str(project_root()),
        "--approval",
        "prompt",
        "--no-probe",
    ]
    if not command:
        fragment = config.data_dir / "openclaw-mcp-fragment.json"
        atomic_write_json(fragment, {"mcp": {"servers": {SERVER_NAME: {"command": sys.executable, "args": [str(launcher), "mcp"], "cwd": str(project_root())}}}})
        return {"ok": False, "status": "NOT_APPLICABLE", "fragment": str(fragment), "message": "OpenClaw nicht gefunden; Fragment wurde erzeugt."}
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "status": "BLOCKED", "message": str(exc)}
    if result.returncode != 0:
        return {"ok": False, "status": "BLOCKED", "exit_code": result.returncode, "stdout": result.stdout[-1000:], "stderr": result.stderr[-1000:]}
    return {"ok": True, "status": "PASS", "stdout": result.stdout[-1000:]}


def setup(config: BridgeConfig, mode: str = "claude-host") -> dict[str, Any]:
    config.ensure_dirs()
    if not config.config_path or not config.config_path.exists():
        config.save()
    result: dict[str, Any] = {"mode": mode, "config": str(config.config_path), "steps": []}
    if mode in {"claude-host", "ui"}:
        result["steps"].append({"name": "claude_desktop_mcp", **install_claude_mcp(config)})
    if mode == "openclaw-host":
        result["steps"].append({"name": "openclaw_mcp", **openclaw_add_mcp(config)})
    if mode == "ui":
        result["steps"].append({"name": "web_ui", "command": f"{sys.executable} {project_root() / 'scripts' / 'genesis-bridge.py'} web"})
    manifest = config.data_dir / "setup-manifest.json"
    atomic_write_json(manifest, result)
    result["manifest"] = str(manifest)
    return result
