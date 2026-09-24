# Requirements Traceability

| ID | Requirement | Implementierung | Test/Gate | Status |
|---|---|---|---|---|
| REQ-001 | Datei einmal einlesen, Hash bilden | `shared.py`, `bundle.py` | Core-/Bundle-Tests | implemented |
| REQ-002 | Ollama native API | `ollama.py` | Fake-Ollama | implemented |
| REQ-003 | automatische Modellwahl | `ollama.py` | Provider-Test | implemented |
| REQ-004 | OpenClaw ohne Shell-Injection | `openclaw.py` | Adapter review | implemented |
| REQ-005 | MCP stdio | `mcp_server.py` | MCP-Tests | implemented |
| REQ-006 | Claude-Konfiguration mit Backup | `installer.py` | Installer-Tests | implemented |
| REQ-007 | Loopback-only UI | `web.py` | UI-HTTP-Smoke | implemented |
| REQ-008 | aktuelle Laufdaten statt Workspace-Müll | `cleanup.py`, `orchestrator.py` | Cleanup-Test | implemented |
| REQ-009 | Diagnose-Neustart von vorn | `doctor.py` | Doctor-Test | implemented |
| REQ-010 | ZIP vollständig inklusive verschachtelter Inhalte prüfen | `bundle.py` | `test_zip_and_nested_zip_are_fully_flattened` | implemented |
| REQ-011 | Verzeichnisse rekursiv prüfen | `bundle.py`, `orchestrator.py` | Directory-Bundle-Test | implemented |
| REQ-012 | Uploads mehrerer Dateien und Browser-Ordner | `web.py`, `bundle.py` | UI/API review | implemented |
| REQ-013 | Korrektur erst nach Vorschlag und ausdrücklicher Bestätigung | `corrections.py`, `web.py`, `mcp_server.py` | Correction-Tests | implemented |
| REQ-014 | Originale niemals überschreiben | `CorrectionManager` | Originalschutz-Test | implemented |
| REQ-015 | `Korrekturen/<Programm>/<Zeitstempel>` neben Quelle | `corrections.py` | Target-/Plan-Test | implemented |
| REQ-016 | korrigierte ZIP plus Dokumentation | `corrections.py` | ZIP-correction-Test | implemented |
| REQ-017 | echte Windows-VM-Prüfung | Zielrechner/Hyper-V | `verify.ps1 -Live` | BLOCKED here |
| REQ-018 | Ausgabe ohne Fake-Claims | Statusmodell/README | Review | implemented |
