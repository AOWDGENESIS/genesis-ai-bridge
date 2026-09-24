# Security Policy

Genesis AI Bridge ist für lokale Einzelbenutzung ausgelegt. Die UI darf nur auf Loopback gebunden werden. Bitte keine Ports ins LAN oder Internet weiterleiten.

Melde Sicherheitsprobleme nicht zusammen mit echten Schlüsseln, Tokens oder privaten Dateien. Entferne Secrets aus Reproduktionen. Bis zu einer öffentlichen Kontaktadresse werden Issues im privaten Repository bzw. direkt an den Betreiber gemeldet.

Die Bridge liest keine Claude-/Ollama-Credentials aus Dateien. `ANTHROPIC_API_KEY` wird nur aus der Prozessumgebung gelesen. MCP blockiert standardmäßig Credential-Dateinamen. Die Anwendung ersetzt keine OS-Sandbox oder VM; untrusted Repositories sollen weiterhin in einer echten VM geprüft werden.
