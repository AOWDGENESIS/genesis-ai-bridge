# Projektverfassung

## Zweck
Genesis AI Bridge verbindet einen lokalen Ollama-Dienst mit einem MCP-fähigen Host (Claude Desktop/Code oder OpenClaw) und optional einer Anthropic-API. Die Bridge ist Orchestrierung, Validierung und Evidenzschicht; sie ist kein Ersatz für die Modelle.

## Nicht verhandelbare Regeln

1. **Sicherheit vor Komfort:** Keine LAN-Exposition, keine Credential-Extraktion, keine Shell-Ausführung aus Modelltext.
2. **Evidence-first:** PASS, FAIL, BLOCKED, NOT_APPLICABLE und NOT_TESTED werden getrennt geführt.
3. **Kanonische Eingabe:** Ein Lauf bekommt eine unveränderte Bytefolge und einen SHA-256. Jede Providerantwort bezieht sich auf diesen Hash.
4. **Reversibilität:** Konfigurationsänderungen werden atomar geschrieben und vorher gesichert.
5. **Benutzerhoheit:** Keine Installation unbekannter Pakete, keine Firewall-/Registryänderung, kein automatischer Modell-Download.
6. **Loopback-only:** Lokale APIs werden über 127.0.0.1 angesprochen; das Server-Binding von Ollama wird nicht ungefragt umkonfiguriert.
7. **Kein Prompt als Sicherheitskontrolle:** Dateiinhalte und Modellantworten sind untrusted data; technische Grenzen liegen in Code und Betriebssystem.
8. **Workspace-Hygiene:** Laufzeitdaten liegen außerhalb des Source-Repositories und werden auf den letzten Bericht begrenzt.
9. **Anti-Endlosschleife:** Nach maximal fünf fehlgeschlagenen Reparaturversuchen wird BLOCKED dokumentiert.
10. **Ehrlichkeit:** Eine echte Windows-VM-Prüfung darf erst nach realer Ausführung als PASS bezeichnet werden.

## Zielplattform
Primär Windows 11 x64 mit Ollama und Claude Desktop; Kernlogik bleibt Python- und plattformübergreifend.

## Qualitätsstandard
Stdlib-only Kern, UTF-8, atomare Dateien, explizite Timeouts, strukturierte Ergebnisse, unittest, compileall, MCP-JSON-RPC-Handshake und lokaler Fake-Provider-Test.
