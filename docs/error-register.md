# Fehlerregister

| ID | Status | Schweregrad | Befund | Fix | Verifikation |
|---|---|---|---|---|---|
| ERR-INIT-001 | VERIFIED | HIGH | Unterminierter String in `shared.py` | Rückgabezeichenkette korrekt geschlossen | RUN 3 und RUN 4 compileall + Tests PASS |
| ERR-TEST-002 | VERIFIED | MEDIUM | Drei Testannahmen waren falsch (Hashwerte/Fehlergrenze) | erwartete SHA-256-Werte berechnet; Orchestrator-Fehlerstatus korrekt geprüft | RUN 3 bis RUN 6 Tests PASS |
| ERR-BUNDLE-001 | VERIFIED | HIGH | Einzeldatei-Workflow prüfte ZIP-/Ordnerinhalte nicht vollständig | `bundle.py` plus rekursive Orchestrator-Analyse für Datei, Ordner, Upload und ZIP | RUN 6 Bundle-/Traversal-/Nested-ZIP-Tests PASS |
| ERR-CORRECTION-001 | VERIFIED | HIGH | Es gab keinen sicheren Vorschlag-/Bestätigungs-/Zielordner-Workflow | `corrections.py`, UI-/MCP-Bestätigung, Hashvergleich, Korrekturplan und Originalschutz | RUN 6 Correction-Tests PASS |
| ERR-ENV-001 | BLOCKED | HIGH | Vollständige Windows-Clean-VM steht in der Agent-Sandbox nicht zur Verfügung | kein unsicherer Workaround; Windows-Prüfscripte bereitgestellt | `scripts/verify.ps1 -Live` auf Zielrechner erforderlich |
