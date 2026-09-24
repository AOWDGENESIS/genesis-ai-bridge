# TEST LEDGER

## RUN 6 — 2026-09-06 — Arena Sandbox

| TEST-ID | Befehl/Aktion | Erwartet | Tatsächlich | Status | Evidenz |
|---|---|---|---|---|---|
| SYNTAX-001 | `PYTHONPATH=src python -m compileall -q src tests` | Exit 0 | Exit 0 | PASS | RUN 6 terminal |
| UNIT-001..020 | `PYTHONPATH=src python -m unittest discover -s tests -v` | alle Tests grün | 20/20 grün | PASS | `tests/` inklusive `test_bundle_corrections.py` |
| BUNDLE-001 | rekursiver Directory-Bundle-Test | Unterordner und Dateien enthalten | `one/two/file.txt` enthalten; `.env`/Symlink übersprungen | PASS | Bundle-Test |
| BUNDLE-002 | ZIP + verschachteltes ZIP | alle inneren Daten als Einträge | `root.txt` und `inner.zip/nested/file.txt` analysierbar | PASS | Nested-ZIP-Test |
| SEC-BUNDLE-001 | ZIP-Traversal-/Drive-/UNC-Pfade | nicht akzeptieren | `../`, `C:/` und UNC rejected | PASS | Security-Bundle-Test |
| CORR-001 | Korrekturvorschlag + Originalschutz | neue Struktur, Original unverändert | neuer Zielordner, Original `old` blieb `old` | PASS | Correction-Test |
| CORR-002 | ZIP-Korrektur | korrigierte ZIP plus Plan | `<name>.korrigiert.zip` und `Korrekturplan.json` erzeugt | PASS | ZIP-Correction-Test |
| CORR-003 | Bestätigungs-Gate | `confirmed=false` schreibt nichts | ValueError; erst `true` erzeugt Ziel | PASS | Orchestrator-Correction-Test |
| MCP-001 | initialize + tools/list über stdin/stdout | valides JSON-RPC und Korrekturtools sichtbar | Handshake PASS; 6 Tools inkl. Vorschlag/Anwendung | PASS | MCP-Smoke |
| META-001 | `tomllib` + `json.loads` | parsebar | JSON/default config parsebar | PASS | RUN 6 terminal |
| SEC-001 | Scan auf `shell=True`, `os.system`, `eval`, `exec` | keine unsicheren Aufrufe | keine Treffer | PASS | RUN 6 terminal |
| CLEAN-001 | Orchestrator-Lauf mit Fake-Ollama | nur aktueller Bericht | `runs` nach Lauf leer; latest report vorhanden | PASS | `test_orchestrator_writes_only_latest_report` |
| UI-001 | Webserver auf `127.0.0.1:8799`; GET `/api/health` und `/` | Health JSON + HTML | beide Requests 200; HTML enthält `webkitdirectory` | PASS | RUN 6 curl-Smoke |
| UX-001 | `START_HIER.bat`, README und neue UI-Felder statisch geprüft | ein verständlicher Startweg | Datei/ZIP/Ordner/Mehrfachupload, lokaler Pfad und Bestätigung dokumentiert | PASS | RUN 6 review |
| VM-001 | Windows 11 Clean-Machine/VM | echte Installation/MCP/GUI | Umgebung hat kein Windows/VM-Tool | BLOCKED | `docs/progress.md` |
| LIVE-001 | echter Ollama-Chat auf GENESIS | echter Provider-Nachweis | in Sandbox kein Ollama | NOT TESTED | `scripts/verify.ps1 -Live` erforderlich |
| LIVE-002 | echter OpenClaw-/Claude-Desktop-Lauf | echte Zielintegration | OpenClaw nicht nachgewiesen; kein Claude-Desktop-Livezugriff | NOT TESTED | Zielrechner erforderlich |

## Vorherige Runs

- RUN 1: compileall FAIL — unterminierter String in `shared.py`; behoben.
- RUN 2: 3 Testfehler — falsche Test-Hashes und falsche Erwartung, dass Orchestrator Providerfehler wirft; Tests korrigiert.
- RUN 3: kompletter Core-/MCP-/Metadaten-/Security-Lauf PASS.
- RUN 4: kompletter Lauf inklusive UI-HTTP-Smoke PASS.
- RUN 5: Volltest nach Launcher-Vereinfachung, 14/14 PASS.
- RUN 6: vollständige Neubewertung ab Test 1 nach Bundle-/Korrekturintegration, 20/20 PASS.

`FINAL / 100 %` ist wegen VM-001, LIVE-001 und LIVE-002 ausdrücklich **nicht** freigegeben.
