from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from .config import BridgeConfig
from .doctor import Doctor
from .installer import setup
from .orchestrator import BridgeOrchestrator
from .web import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="genesis-ai-bridge", description="Genesis AI Bridge")
    parser.add_argument("--config", help="Pfad zur JSON-Konfiguration")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Verbindung und Konfiguration prüfen")
    loop = sub.add_parser("verify-loop", help="Prüfen, sichere lokale Reparaturen ausführen und von vorn beginnen")
    loop.add_argument("--rounds", type=int, default=5)
    setup_parser = sub.add_parser("setup", help="Claude Desktop/OpenClaw sicher konfigurieren")
    setup_parser.add_argument("--mode", choices=["claude-host", "openclaw-host", "ui"], default="claude-host")
    web_parser = sub.add_parser("web", help="Lokale Weboberfläche starten")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8787)
    sub.add_parser("mcp", help="MCP-stdio-Server starten")
    run = sub.add_parser("run", help="Eine Datei an konfigurierte Provider senden")
    run.add_argument("file", type=Path)
    run.add_argument("--task", default="Prüfe die Datei vollständig, finde Fehler und Warnungen und schlage sichere Korrekturen vor.")
    run.add_argument("--provider", action="append", choices=["ollama", "openclaw", "anthropic"], dest="providers")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = BridgeConfig.load(args.config)
    if args.command == "doctor":
        findings = Doctor(config).check()
        print(json.dumps({"ok": not any(item.level in {"ERROR", "WARNING"} for item in findings), "findings": [item.as_dict() for item in findings]}, ensure_ascii=False, indent=2))
        return 0 if not any(item.level in {"ERROR", "WARNING"} for item in findings) else 1
    if args.command == "verify-loop":
        result = Doctor(config).run_until_clean(args.rounds)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    if args.command == "setup":
        print(json.dumps(setup(config, args.mode), ensure_ascii=False, indent=2))
        return 0
    if args.command == "web":
        serve(config, args.host, args.port)
        return 0
    if args.command == "mcp":
        from .mcp_server import run_stdio

        return run_stdio(config)
    if args.command == "run":
        result = BridgeOrchestrator(config).run_path(args.file, args.task, args.providers)
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
        return 0 if result.status in {"complete", "partial"} else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
