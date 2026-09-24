# Testplan

## Automatisch in dieser Umgebung

1. Python-Compile-/Importprüfung.
2. Artefakt-Hash, UTF-8/BOM und Chunking.
3. Deterministischer Fake-Ollama-HTTP-Server: Health, Tags, Show, Chat.
4. Orchestrator mit Fake-Ollama, inklusive SHA-Hash und latest report.
5. Rekursiver Verzeichnis-Bundle-Test.
6. ZIP-Vollständigkeit, verschachtelte ZIP-Inhalte, Traversal-/Laufwerkspfad-Schutz.
7. Symlink-/Credential-Überspringen bei Verzeichnissen und Archiven.
8. Expliziter Korrekturvorschlag, Originalschutz, Korrekturplan und ZIP-Neuschreibung.
9. MCP JSON-RPC: initialize, tools/list, tools/call, stdout-Protokoll.
10. MCP Pfad- und Credential-Schutz.
11. Claude-JSON-Konfigurationsmerge und Backup.
12. Doctor-Runden ohne Endlosschleife.
13. Loopback-Webserver-Policy sowie GET `/api/health` und UI-HTML-Smoke.
14. Security-Scan gegen `shell=True`, `os.system`, `eval`, `exec`.

## Zielrechner Windows 11

- `scripts/verify.ps1` ohne `-Live`.
- Ollama-Live-Health, `/api/tags`, `/api/show`, echter kurzer Chat.
- `setup.ps1` auf Kopie der Claude-Konfiguration; danach echte Claude-Desktop-MCP-Verbindung.
- OpenClaw nur, wenn installiert: `openclaw mcp doctor --probe` und ein einzelner Agent-Lauf.
- Datei, ZIP, verschachteltes ZIP, Browser-Ordnerauswahl und lokaler Quellpfad; Originalschutz und Zielordner im Explorer prüfen.
- Dateien aus Inventur: Umlaute, 130-KB-/212-KB-TXT, Bilddatei, JSON/YAML, ungültige UTF-8-Datei.
- Clean-Machine/VM: neues Standardbenutzerprofil ohne Python-/Node-/Git-Entwicklungsreste.
- negativer Test: Ollama aus, falsches Modell, Timeout, volle/gesperrte Datei, ungültige Claude-JSON-Datei, ZIP-Traversal und Symlink.

## Release-Gate

`FINAL` ist hier nicht zulässig, solange die Windows-Clean-Machine-Prüfung nicht tatsächlich durchgeführt und dokumentiert ist. Aktueller Nachweis: Linux-Core-/Bundle-/Korrekturtests möglich; Windows-VM-Gate BLOCKED.
