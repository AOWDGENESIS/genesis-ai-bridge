# Spezifikation

## User Stories

- **US-001:** Als Nutzer wähle ich eine Datei, ein ZIP, mehrere Dateien oder einen übergeordneten Ordner und erhalte eine vollständige Prüfung.
- **US-002:** ZIP-Inhalte einschließlich möglicher verschachtelter Archive werden als eigene relative Bundle-Einträge geprüft; unsichere Pfade und Symlinks werden nicht extrahiert/folgt.
- **US-003:** Als Nutzer sehe ich Hash/Manifest, jeden Bundle-Eintrag, Provider, Modell, Status, Dauer, Warnungen und Ergebnis getrennt.
- **US-004:** Als Nutzer erhalte ich nach der Analyse zuerst nur einen maschinenvalidierten Korrekturvorschlag.
- **US-005:** Als Nutzer kann ich den Vorschlag ausdrücklich bestätigen; die Bridge erstellt dann einen neuen Korrekturordner und verändert keine Originale.
- **US-006:** Als Nutzer kann ich eine Programmbezeichnung und optional den lokalen Originalpfad angeben.
- **US-007:** Als Browser-Nutzer werde ich informiert, wenn kein echter lokaler Quellpfad bekannt ist und deshalb ein externer Korrekturordner verwendet wird.
- **US-008:** Als Claude-Desktop-Nutzer kann ich die Bridge als lokalen MCP-Server nutzen.
- **US-009:** Als OpenClaw-Nutzer kann ich die Bridge über den dokumentierten MCP-Registry-Weg anbinden; OpenClaw bleibt ein eigenes, optionales Ziel.

## Abnahme

- Eine Datei mit Umlauten und Zeilenumbrüchen erzeugt denselben SHA-256 in allen Ergebnissen.
- ZIP- und verschachtelte ZIP-Dateien werden vollständig bis zum konfigurierten Archiv-Tiefenlimit erfasst.
- Absolute Pfade, Laufwerkspfade, `..`, Symlinks und überschrittene Größen-/Eintragslimits werden nicht als vertrauenswürdige Dateien behandelt.
- Ein rekursives Verzeichnis erhält einen Eintrag pro Datei und erhält Unterordnerpfade.
- Ollama wird über `/api/chat` mit `stream: false`, begrenztem Kontext, Temperatur und Timeout angesprochen.
- Ein fehlender optionaler Provider führt nicht zu einer erfundenen Erfolgsmeldung.
- Ein Korrekturvorschlag kann nur auf bereits geprüfte relative Pfade zeigen und wird vor Bestätigung nicht geschrieben.
- Nach Bestätigung liegen Korrekturen unter `Korrekturen/<Programm>/<Zeitstempel>`; ein `Korrekturplan.json` enthält Ausgangs-Hash, Zielpfad und Änderungen.
- Eine ungültige Claude-Konfiguration wird nicht überschrieben.
- MCP `initialize`, `tools/list` und `tools/call` funktionieren per stdin/stdout; Logs gehen nicht auf stdout.
- Ein Lauf lässt im Source-Repository keine Laufdaten zurück.
- Bei Fehlern des Fake-Ollama-Servers wird ein FAIL/partial-Ergebnis erzeugt.
- Ein nicht ausführbarer Windows-VM-Test bleibt BLOCKED/NOT_TESTED.

## Nicht-Ziele

- Kein Browser-/Desktop-RPA für Claude.
- Keine automatische Modellinstallation ohne Nutzerfreigabe.
- Kein eigener Parser für jedes Office-Format in Version 0.1; Binärdateien erhalten ehrliche Metadatenanalyse.
- Kein öffentlich erreichbarer Server, kein Mehrbenutzer-/Cloudbetrieb.
- Keine Korrektur von nicht geprüften, neu erfundenen oder externen Pfaden.
