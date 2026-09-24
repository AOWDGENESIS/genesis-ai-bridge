from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import atomic_write_json, expand_path


DEFAULTS: dict[str, Any] = {
    "ollama_base_url": "http://127.0.0.1:11434",
    "ollama_model": "auto",
    "ollama_timeout_seconds": 300,
    "ollama_num_ctx": 16384,
    "ollama_keep_alive": "15m",
    "ollama_temperature": 0.1,
    "openclaw_command": "openclaw",
    "openclaw_agent": "main",
    "openclaw_timeout_seconds": 600,
    "anthropic_model": "claude-sonnet-4-6",
    "anthropic_api_key_env": "ANTHROPIC_API_KEY",
    "max_file_bytes": 32 * 1024 * 1024,
    "max_bundle_bytes": 256 * 1024 * 1024,
    "max_bundle_entries": 2000,
    "max_archive_depth": 3,
    "max_correction_files": 200,
    "max_input_chars": 80_000,
    "chunk_chars": 14_000,
    "max_synthesis_chars": 60_000,
    "data_dir": "",
    "synthesis_provider": "auto",
    "mcp_allowed_roots": [],
    "strict_doctor": True,
}


def default_data_dir() -> Path:
    explicit = os.environ.get("GENESIS_BRIDGE_DATA")
    if explicit:
        return expand_path(explicit)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        return expand_path(Path(base) / "GenesisAI" / "Bridge")
    base = os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")
    return expand_path(Path(base) / "genesis-ai-bridge")


def default_config_path() -> Path:
    explicit = os.environ.get("GENESIS_BRIDGE_CONFIG")
    if explicit:
        return expand_path(explicit)
    return default_data_dir() / "config.json"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass
class BridgeConfig:
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    ollama_num_ctx: int
    ollama_keep_alive: str
    ollama_temperature: float
    openclaw_command: str
    openclaw_agent: str
    openclaw_timeout_seconds: int
    anthropic_model: str
    anthropic_api_key_env: str
    max_file_bytes: int
    max_bundle_bytes: int
    max_bundle_entries: int
    max_archive_depth: int
    max_correction_files: int
    max_input_chars: int
    chunk_chars: int
    max_synthesis_chars: int
    data_dir: Path
    synthesis_provider: str
    mcp_allowed_roots: tuple[Path, ...] = field(default_factory=tuple)
    strict_doctor: bool = True
    config_path: Path | None = None

    @classmethod
    def load(cls, path: str | Path | None = None) -> "BridgeConfig":
        config_path = expand_path(path) if path else default_config_path()
        values = dict(DEFAULTS)
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if not isinstance(loaded, dict):
                raise ValueError("Die Bridge-Konfiguration muss ein JSON-Objekt sein.")
            values.update(loaded)
        data_dir_value = values.get("data_dir") or str(default_data_dir())
        roots = values.get("mcp_allowed_roots") or []
        if not isinstance(roots, list):
            raise ValueError("mcp_allowed_roots muss eine Liste sein.")
        return cls(
            ollama_base_url=str(values["ollama_base_url"]),
            ollama_model=str(values["ollama_model"]),
            ollama_timeout_seconds=int(values["ollama_timeout_seconds"]),
            ollama_num_ctx=int(values["ollama_num_ctx"]),
            ollama_keep_alive=str(values["ollama_keep_alive"]),
            ollama_temperature=float(values["ollama_temperature"]),
            openclaw_command=str(values["openclaw_command"]),
            openclaw_agent=str(values["openclaw_agent"]),
            openclaw_timeout_seconds=int(values["openclaw_timeout_seconds"]),
            anthropic_model=str(values["anthropic_model"]),
            anthropic_api_key_env=str(values["anthropic_api_key_env"]),
            max_file_bytes=int(values["max_file_bytes"]),
            max_bundle_bytes=int(values["max_bundle_bytes"]),
            max_bundle_entries=int(values["max_bundle_entries"]),
            max_archive_depth=int(values["max_archive_depth"]),
            max_correction_files=int(values["max_correction_files"]),
            max_input_chars=int(values["max_input_chars"]),
            chunk_chars=int(values["chunk_chars"]),
            max_synthesis_chars=int(values["max_synthesis_chars"]),
            data_dir=expand_path(data_dir_value),
            synthesis_provider=str(values["synthesis_provider"]),
            mcp_allowed_roots=tuple(expand_path(item) for item in roots),
            strict_doctor=bool(values.get("strict_doctor", True)),
            config_path=config_path,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "ollama_timeout_seconds": self.ollama_timeout_seconds,
            "ollama_num_ctx": self.ollama_num_ctx,
            "ollama_keep_alive": self.ollama_keep_alive,
            "ollama_temperature": self.ollama_temperature,
            "openclaw_command": self.openclaw_command,
            "openclaw_agent": self.openclaw_agent,
            "openclaw_timeout_seconds": self.openclaw_timeout_seconds,
            "anthropic_model": self.anthropic_model,
            "anthropic_api_key_env": self.anthropic_api_key_env,
            "max_file_bytes": self.max_file_bytes,
            "max_bundle_bytes": self.max_bundle_bytes,
            "max_bundle_entries": self.max_bundle_entries,
            "max_archive_depth": self.max_archive_depth,
            "max_correction_files": self.max_correction_files,
            "max_input_chars": self.max_input_chars,
            "chunk_chars": self.chunk_chars,
            "max_synthesis_chars": self.max_synthesis_chars,
            "data_dir": str(self.data_dir),
            "synthesis_provider": self.synthesis_provider,
            "mcp_allowed_roots": [str(item) for item in self.mcp_allowed_roots],
            "strict_doctor": self.strict_doctor,
        }

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "runs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)

    def save(self) -> Path:
        path = self.config_path or default_config_path()
        atomic_write_json(path, self.to_dict())
        self.config_path = path
        return path

    @property
    def latest_json(self) -> Path:
        return self.data_dir / "latest.json"

    @property
    def latest_markdown(self) -> Path:
        return self.data_dir / "latest.md"

    @property
    def report_dir(self) -> Path:
        return self.data_dir / "reports"
