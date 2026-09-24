# Technischer Plan

## Komponenten

```text
CLI / PowerShell
       |
Web UI (127.0.0.1) ---- Orchestrator ---- Bundle-Inspector
MCP stdio -------------/       |          |-- Datei/Upload
                                |          |-- rekursives Verzeichnis
                                |          |-- ZIP/Nested-ZIP, sichere Limits
                                |
                         Ollama / OpenClaw / Anthropic
                                |
                    Analyse je Bundle-Eintrag + Synthese
                                |
              Korrekturvorschlag --confirmed=true--> CorrectionManager
                                |
       Korrekturen/<Programm>/<Zeitstempel>/ + Korrekturplan.json
```

## Providerstrategie

- Ollama: Pflicht-/Standardprovider, native `/api/chat`, Live-Modell-Discovery via `/api/tags` und `/api/show`.
- OpenClaw: optionaler CLI-Adapter, keine Shell, separates Timeout, JSON-/Text-Fallback.
- Anthropic: optional nur per `ANTHROPIC_API_KEY`; Schlüssel wird nicht geschrieben.
- Claude Desktop: MCP-Host, nicht als heimlich fernsteuerbares Modell-API behandelt.

## Bundle- und Transaktionsfluss

1. Eingabe wird gelesen; Datei-, Bundle-, Eintrags- und Archiv-Tiefenlimits werden geprüft.
2. Verzeichnisse werden rekursiv gelesen; Archive werden nur mit sicheren relativen Pfaden verarbeitet.
3. Jede Datei erhält MIME, Text-/Binärmetadaten, SHA-256 und einen relativen Pfad.
4. Große Texte werden deterministisch geteilt; jeder Bundle-Eintrag wird separat analysiert.
5. Provider erhalten dieselben Bundle-Einträge und dieselbe Aufgabe; Dateiinhalte bleiben untrusted data.
6. `latest.json` und `latest.md` dokumentieren Bundle, Einträge, Provider, Warnungen und Synthese.
7. Ein Korrekturvorschlag darf nur geprüfte Pfade und `replace` enthalten; bis zur Bestätigung wird nichts geschrieben.
8. Vor Anwendung wird der Ausgangs-Manifest-Hash erneut verglichen.
9. Der CorrectionManager kopiert die geprüften Inhalte in einen neuen Zielordner, wendet die bestätigten Änderungen dort an, erzeugt bei ZIP-Quellen eine korrigierte ZIP und schreibt `Korrekturplan.json`.

## Bewusste Vereinfachung

Der Kern verwendet ausschließlich die Python-Standardbibliothek. So entfällt eine unkontrollierte Paket-Supply-Chain für die lokale Bridge. Ein Installer/venv kann später ergänzt werden, ist für Version 0.1 nicht nötig.
