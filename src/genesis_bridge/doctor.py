from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import BridgeConfig
from .ollama import OllamaClient, ProviderError, normalized_base_url
from .openclaw import OpenClawClient
from .paths import is_within


@dataclass
class Finding:
    level: str
    code: str
    message: str
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"level": self.level, "code": self.code, "message": self.message, "details": self.details or {}}


class Doctor:
    def __init__(self, config: BridgeConfig | None = None) -> None:
        self.config = config or BridgeConfig.load()
        self.ollama = OllamaClient(self.config)
        self.openclaw = OpenClawClient(self.config)

    def check(self) -> list[Finding]:
        findings: list[Finding] = []
        if sys.version_info < (3, 10):
            findings.append(Finding("ERROR", "PYTHON_VERSION", "Python 3.10 oder neuer ist erforderlich."))
        else:
            findings.append(Finding("PASS", "PYTHON_VERSION", f"Python {sys.version.split()[0]} ist geeignet."))
        try:
            self.config.ensure_dirs()
            findings.append(Finding("PASS", "DATA_DIR", f"Laufzeitordner ist verfügbar: {self.config.data_dir}"))
        except OSError as exc:
            findings.append(Finding("ERROR", "DATA_DIR", f"Laufzeitordner kann nicht angelegt werden: {exc}"))
        try:
            usage = shutil.disk_usage(self.config.data_dir)
            if usage.free < 100 * 1024 * 1024:
                findings.append(Finding("ERROR", "DISK_SPACE", "Weniger als 100 MB frei im Laufzeitvolume."))
            else:
                findings.append(Finding("PASS", "DISK_SPACE", f"Freier Speicher: {usage.free / 1024**3:.2f} GB."))
        except OSError as exc:
            findings.append(Finding("WARNING", "DISK_SPACE", f"Freier Speicher konnte nicht geprüft werden: {exc}"))

        try:
            health = self.ollama.health()
            if health.get("ok"):
                findings.append(Finding("PASS", "OLLAMA_HEALTH", f"Ollama antwortet unter {self.ollama.base_url}."))
                try:
                    models = self.ollama.inspect_models()
                    if not models:
                        findings.append(Finding("ERROR", "OLLAMA_MODELS", "Ollama läuft, aber kein Modell ist installiert."))
                    else:
                        selected = self.ollama.choose_model()
                        findings.append(Finding("PASS", "OLLAMA_MODEL", f"Modellwahl: {selected.name} ({len(models)} Modelle erkannt).", {"models": [item.name for item in models]}))
                except ProviderError as exc:
                    findings.append(Finding("ERROR", "OLLAMA_MODELS", str(exc)))
            else:
                findings.append(Finding("ERROR", "OLLAMA_HEALTH", f"Ollama antwortet unerwartet: {health.get('response')}"))
        except ProviderError as exc:
            findings.append(Finding("ERROR", "OLLAMA_HEALTH", str(exc)))

        if normalized_base_url(self.config.ollama_base_url) != self.config.ollama_base_url.rstrip("/"):
            findings.append(Finding("WARNING", "OLLAMA_ENDPOINT", "Die Bridge verwendet aus Sicherheitsgründen Loopback statt 0.0.0.0/localhost im Client-Endpunkt."))
        else:
            findings.append(Finding("PASS", "OLLAMA_ENDPOINT", f"Client-Endpunkt ist lokal gebunden: {self.config.ollama_base_url}."))

        openclaw = self.openclaw.doctor()
        if openclaw.get("available"):
            findings.append(Finding("PASS", "OPENCLAW", f"OpenClaw gefunden: {openclaw.get('version', '')}"))
        else:
            findings.append(Finding("NOT_APPLICABLE", "OPENCLAW", "OpenClaw ist nicht installiert; Ollama-only/Claude-MCP-Betrieb bleibt möglich."))

        if os.environ.get(self.config.anthropic_api_key_env):
            findings.append(Finding("INFO", "ANTHROPIC", "Anthropic API-Schlüssel ist nur über die Umgebung verfügbar; er wird nicht gespeichert."))
        else:
            findings.append(Finding("NOT_APPLICABLE", "ANTHROPIC", f"{self.config.anthropic_api_key_env} ist nicht gesetzt; direkte Anthropic-API ist deaktiviert."))

        if os.environ.get("GENESIS_BRIDGE_NESTED") == "1":
            findings.append(Finding("INFO", "RECURSION_GUARD", "Rekursionsschutz ist aktiv."))
        return findings

    def repair_safe(self, findings: list[Finding]) -> list[str]:
        repairs: list[str] = []
        # Only reversible local repairs are automatic. Provider installation, firewall changes,
        # secret handling and global environment changes intentionally require the user.
        try:
            self.config.ensure_dirs()
            repairs.append("Laufzeitordner sichergestellt")
        except OSError:
            pass
        return repairs

    def run_until_clean(self, max_rounds: int = 5) -> dict[str, Any]:
        history: list[dict[str, Any]] = []
        for round_no in range(1, max_rounds + 1):
            findings = self.check()
            repairs = self.repair_safe(findings)
            history.append({"round": round_no, "findings": [item.as_dict() for item in findings], "repairs": repairs})
            blocking = [item for item in findings if item.level in {"ERROR", "WARNING"}]
            if not blocking:
                return {"ok": True, "rounds": round_no, "history": history}
            if not repairs:
                return {"ok": False, "rounds": round_no, "history": history, "blocked_by": [item.as_dict() for item in blocking]}
        return {"ok": False, "rounds": max_rounds, "history": history, "blocked_by": "max_rounds"}
