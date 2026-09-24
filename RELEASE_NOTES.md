# Release Notes 0.1.0

## Status

**NICHT FINAL / Source Preview.** Core-, Bundle- und Korrekturtests sowie lokale Simulatorprüfungen sind grün. Eine echte Windows-Clean-Machine, Claude-Desktop-MCP-Verbindung, OpenClaw-Verbindung und Ollama-Live-Prüfung wurden in der Agent-Sandbox nicht ausgeführt.

## Enthalten

- `scripts/install.ps1` für die lokale Einrichtung
- `scripts/verify.ps1` für Compile-, Test- und optionalen Live-Lauf
- `scripts/start-ui.ps1` für die Loopback-UI
- `scripts/genesis-bridge.py mcp` als MCP-stdio-Server
- rekursive Bundle-Prüfung für Dateien, Ordner, Upload-Auswahl, ZIP und verschachtelte ZIP-Inhalte
- sichere Archivgrenzen gegen absolute Pfade, Traversal, Symlinks, zu viele Einträge, zu große Inhalte und zu große Archivtiefe
- Korrekturvorschlag ohne Schreibzugriff sowie ausdrücklicher Bestätigungsworkflow
- neue Zielordner `Korrekturen/<Programmbezeichnung>/<Zeitstempel>` und `Korrekturplan.json`
- korrigierte ZIP-Ausgabe, ohne Originalarchiv zu überschreiben

## Nächster Abnahmeschritt

Auf dem Inventurrechner `scripts/verify.ps1 -Live`, danach `scripts/install.ps1 -Mode claude-host`, Claude Desktop vollständig neu starten und die MCP-Tools sichtbar prüfen. Erst danach kann ein Windows-VM-Gate bewertet werden.
