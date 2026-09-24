# Threat Model

| Asset | Bedrohung | Kontrolle | Nachweis |
|---|---|---|---|
| lokale Datei | Path traversal / Secret-Leak | MCP-Roots, sensitive-name deny, explizite Datei | `test_mcp_path_policy` |
| Ollama | LAN-Missbrauch | Client normalisiert auf Loopback; UI bindet Loopback | `test_normalized_base_url` |
| Claude-Konfiguration | Korruption / Clobber | JSON-Parse vor Änderung, Backup, atomarer Replace | Installer-Tests |
| Providerantwort | Prompt injection / Fake-Erfolg | Output bleibt Text, keine Ausführung, Evidence-Status | Prompt-/Spezifikationstest |
| OpenClaw CLI | Command injection | Argumentliste, `shell=False`, feste Subcommands | Code-Review/Test |
| API-Key | Exfiltration | nur Environment, kein Log/JSON/Report | Code-Review |
| Laufzeitordner | ungebremstes Wachstum | externe Daten, `runs` je Lauf geleert, 20-MB-Prune | Cleanup-Test |
| MCP stdout | Protokollkorruption | Logging über stderr/Datei; stdout nur JSON-RPC | MCP-Test |
| Rekursion | OpenClaw ruft Bridge zurück | `GENESIS_BRIDGE_NESTED` Guard und Host-Modi | OpenClaw-Adapter-Test |

## STRIDE-Kurzbewertung

- **Spoofing:** Bridge ist absichtlich lokal; kein Netzwerk-Auth im Loopback-Modus.
- **Tampering:** Konfigurationsbackup und atomare Writes; keine Signatur behauptet.
- **Repudiation:** Lauf-ID, Hash, Zeitstempel und Providerstatus.
- **Information Disclosure:** keine LAN-Bindung; optionale Cloud-Provider sind explizit.
- **Denial of Service:** Dateigröße, Promptgrenzen, Timeouts, Thread-Limit und Circuit Breaker.
- **Elevation of Privilege:** kein `shell=True`, keine Adminanforderung, keine Modellbefehle als Tool.

Restrisiko: Ollama selbst kann vom Betriebssystem bzw. dessen Bind-Adresse aus erreichbar sein. Die Bridge ändert diese globale Einstellung nicht; auf Windows muss der Nutzer die Server-Bindung bei Bedarf separat auf Loopback beschränken.
