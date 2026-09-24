# Risiken

| ID | Risiko | Status | Mitigation |
|---|---|---|---|
| R-001 | Ollama ist mit `0.0.0.0` gebunden und kann LAN-exponiert sein | OPEN / Zielrechner prüfen | Bridge nutzt nur 127.0.0.1; globale Ollama-Bindung nicht ungefragt ändern |
| R-002 | VRAM-Inventur widersprüchlich | OPEN | Live-`/api/show` und kurzer echter Chat; kein blindes großes Defaultmodell |
| R-003 | OpenClaw nicht nachgewiesen | NOT_APPLICABLE bis installiert | optionaler Adapter und Host-Modus |
| R-004 | echte Windows-VM nicht in Agent-Sandbox | BLOCKED | `scripts/verify.ps1 -Live` auf GENESIS/sauberer VM |
| R-005 | Modelloutput kann Prompt-Injection enthalten | MITIGATED | untrusted-data framing; Ausgabe wird nicht ausgeführt |
