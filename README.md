# Genesis AI Bridge

## Für den normalen Betrieb: ein Klick

1. Doppelklick auf **`START_HIER.bat`**.
2. Im Browser eine Datei, ein ZIP, mehrere Dateien oder einen Ordner auswählen.
3. Aufgabe eingeben und **Prüfung starten** drücken.

Für eine Korrektur zeigt die Oberfläche danach zuerst nur einen **Korrekturvorschlag**. Erst nach der ausdrücklichen Bestätigung wird ein neuer Ordner erzeugt. Originaldateien werden nie überschrieben.

## Was geprüft wird

- einzelne Dateien;
- ZIP-Dateien mit allen enthaltenen Dateien;
- verschachtelte ZIP-/JAR-/WHL-/APK-/IPA-Archive bis zur konfigurierten Tiefe;
- übergeordnete Verzeichnisse rekursiv mit Unterordnern;
- mehrere Upload-Dateien und Browser-Ordnerauswahl.

Jeder Bundle-Eintrag erhält einen SHA-256-Hash, MIME-/Textmetadaten und einen eigenen Eintrag im Bericht. ZIP-Einträge werden nicht blind extrahiert: absolute Pfade, Windows-Laufwerkspfade, `..`-Traversal und Symlinks werden abgewiesen oder übersprungen. Größen-, Eintrags- und Archiv-Tiefenlimits schützen vor übergroßen Bundles und Archivbomben.

## Korrekturablauf

1. **Prüfen:** Die ausgewählten Bytes werden analysiert; noch keine Datei wird verändert.
2. **Vorschlag anzeigen:** Die Bridge erstellt aus den vorhandenen Provider-Analysen ein JSON-validiertes, auf bestehende Bundle-Pfade begrenztes Änderungsangebot.
3. **Ausdrücklich bestätigen:** Nur der Bestätigungsbutton wendet sichere `replace`-Änderungen an.
4. **Neuen Ordner prüfen:** Der Zielpfad wird zurückgegeben und zusätzlich in `Korrekturplan.json` dokumentiert.

Bei einem echten lokalen Quellpfad, der in der Oberfläche optional eingetragen werden kann, liegt das Ergebnis neben der Quelle:

```text
<Quellverzeichnis>/
├─ Originale ...
└─ Korrekturen/
   └─ <Programmbezeichnung>/
      └─ <Zeitstempel>/
         ├─ relative/Ordnerstruktur/...
         └─ Korrekturplan.json
```

Bei einer lokalen ZIP-Quelle wird zusätzlich `<name>.korrigiert.zip` erzeugt. Bei verschachtelten ZIP-Einträgen werden die inneren Archive beim Schreiben rekursiv neu aufgebaut.

Ein Browser übermittelt normalerweise keinen absoluten lokalen Pfad. Wenn nur Browser-Dateien hochgeladen werden, meldet die Bridge das transparent und verwendet standardmäßig einen externen Zielbereich unter dem Bridge-Datenordner:

```text
<Bridge-Datenordner>/Korrekturen/<Programmbezeichnung>/<Zeitstempel>/
```

Das ist absichtlich kein Anspruch, neben einer unbekannten Browser-Quelle geschrieben zu haben. Für echte Korrekturen neben der Quelle muss der lokale Pfad auf dem Rechner des laufenden Bridge-Servers zugänglich sein.

## Provider und Betriebsarten

Die Bridge unterstützt **Ollama**, optional **OpenClaw** und optional die **Anthropic API**. OpenClaw und Claude Desktop/Claude Code werden nicht als dasselbe Ziel behandelt. OpenClaw wird nur verwendet, wenn der Befehl gefunden wurde; ein Anthropic-Schlüssel wird ausschließlich aus der konfigurierten Umgebungsvariable gelesen.

- **Lokale UI:** die einfache Standardbedienung über `START_HIER.bat`.
- **Claude Desktop als MCP-Host:** die Bridge stellt einen lokalen stdio-MCP-Server bereit; es wird keine Chat-GUI ferngesteuert.
- **OpenClaw als MCP-Host:** optionale dokumentierte OpenClaw-CLI/MCP-Konfiguration; rekursive Rückrufe werden blockiert.
- **CLI/MCP:** für Diagnose, Automatisierung und Integrationsprüfungen.

Die Weboberfläche bindet nur an Loopback. Für normale Nutzung sind keine PowerShell-Befehle nötig. Die folgenden Befehle sind nur für Diagnose/Entwicklung:

```powershell
py -3 .\scripts\genesis-bridge.py doctor
py -3 .\scripts\genesis-bridge.py verify-loop --rounds 5
py -3 .\scripts\genesis-bridge.py web --host 127.0.0.1 --port 8787
```

## Dateifluss

```text
Datei / ZIP / Verzeichnis / Upload-Auswahl
        ↓
Sicheres Bundle-Manifests + Größen-/Pfad-/Symlink-Prüfung
        ↓
Einzelanalyse je enthaltenem Eintrag
        ↓
Ollama ───────────────┐
OpenClaw oder Claude ─┼─ getrennte Analysen, keine erfundenen Tests
Anthropic optional ───┘
        ↓
Bericht + optionaler KorrekturVORSCHLAG
        ↓ ausdrückliche Bestätigung
neuer Korrekturordner, nie Originale
```

Textdateien werden bei großen Inhalten in Abschnitte geteilt. Wenn das Kontextbudget überschritten wird, wird der ausgelassene Mittelteil im Bericht kenntlich gemacht. Bilder werden als Bilddaten an Ollama übergeben, sofern das Modell dies unterstützt. Unbekannte Binärformate werden nicht als Text erfunden interpretiert.

## Konfiguration

Beim ersten Setup wird eine Konfiguration im Datenordner angelegt. Wichtige Felder:

```json
{
  "ollama_base_url": "http://127.0.0.1:11434",
  "ollama_model": "auto",
  "ollama_num_ctx": 16384,
  "ollama_timeout_seconds": 300,
  "synthesis_provider": "auto",
  "max_file_bytes": 33554432,
  "max_bundle_bytes": 268435456,
  "max_bundle_entries": 2000,
  "max_archive_depth": 3,
  "max_correction_files": 200,
  "mcp_allowed_roots": []
}
```

`ollama_model: auto` bleibt absichtlich aktiv, damit ohne Live-Prüfung kein zu großes Modell als Standard behauptet wird. Laufdaten und Vorschläge werden standardmäßig außerhalb des Repositorys gespeichert; pro Prüf-Lauf bleibt nur der letzte Bericht dauerhaft erhalten.

## Sicherheitsgrenzen

- UI-Bindung ausschließlich an Loopback; keine LAN-Freigabe.
- Credential-/Schlüsseldateien werden nicht automatisch eingelesen oder korrigiert.
- ZIP-Pfade werden normalisiert und gegen absolute Pfade, Laufwerkspfade, `..`, NUL-Zeichen und Symlinks geprüft.
- Symlinks werden weder aus Verzeichnissen gelesen noch in korrigierten ZIPs materialisiert.
- Provideraufrufe nutzen Argumentlisten und `shell=False`.
- Modellantworten sind untrusted data; sie werden nicht als Shell- oder Python-Code ausgeführt.
- Korrekturpfade müssen zu bereits geprüften Einträgen gehören; neue externe Pfade sind verboten.
- Ausgangs-Manifest-Hash wird vor der Anwendung erneut verglichen. Wenn die Quelle geändert wurde, bricht die Bridge ab.
- Korrekturziele werden auf Symlink-Komponenten geprüft und dürfen nicht innerhalb einer lokalen Quellverzeichnisstruktur liegen.

## Grenzen und ehrlicher Teststatus

Ein echter Windows-Clean-Machine-/VM-Test, ein echter Ollama-Live-Endpunkt sowie ein live nachgewiesener OpenClaw-/Claude-Desktop-Lauf sind in der Arena-Linux-Sandbox nicht verfügbar. Die lokale Suite verwendet einen deterministischen Ollama-Simulator und MCP-Protokolltests. Auf dem Zielrechner ist dafür `scripts/verify.ps1 -Live` vorgesehen. Ein fehlendes OpenClaw wird nicht als installiert behauptet.

## Quellen für Integrationsentscheidungen

- OpenClaw Ollama: https://docs.openclaw.ai/providers/ollama
- OpenClaw Agent-CLI: https://docs.openclaw.ai/tools/agent-send
- OpenClaw MCP-CLI: https://docs.openclaw.ai/cli/mcp
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- MCP-JSON-RPC: https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- Ollama API: https://docs.ollama.com/api

## Lizenz

MIT. Siehe `LICENSE`.
