# Annahmen

| ID | Annahme | Grund | Auswirkung | Validierung |
|---|---|---|---|---|
| A-001 | „Open Clowd“ meint wahrscheinlich Claude Desktop bzw. OpenClaw | Inventur zeigt Claude, aber kein OpenClaw | beide Integrationspfade sind enthalten | Zielsystem-Doctor |
| A-002 | Ziel ist primär Windows 11 | KI_INVENTUR | PowerShell-Launcher und Windows-Pfade | Clean-Machine-Test |
| A-003 | Ollama bleibt lokal | Nutzerwunsch und Port 11434 | Loopback, keine Cloudpflicht | `/api/tags` |
| A-004 | Modell darf automatisch aus vorhandenen Modellen gewählt werden | VRAM-Wert widersprüchlich | kein blindes `gemma4:26b` | `/api/show`/echter Chat |
| A-005 | direkte Anthropic-API ist optional | kein API-Key übermittelt | keine Credential-Abfrage im Workspace | Environment-Check |
| A-006 | keine echte Windows-VM im Agent-Sandbox | Tools geprüft: keine Hyper-V/QEMU/Docker | VM-Gate bleibt BLOCKED | auf GENESIS mit `verify.ps1 -Live` |
