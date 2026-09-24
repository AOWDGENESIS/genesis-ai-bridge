# Architecture Decisions

## ADR-001 — Native Ollama API statt `/v1`
**Entscheidung:** `/api/chat` als Standard.
**Grund:** OpenClaw-Dokumentation beschreibt native Ollama-Nutzung; OpenAI-Kompatibilität ist ein separater Kompatibilitätspfad und darf Tool-/Streamingsemantik nicht still verändern.
**Folge:** kleiner eigener HTTP-Adapter, keine OpenAI-SDK-Abhängigkeit.

## ADR-002 — MCP als Claude-Anbindung
**Entscheidung:** Claude Desktop wird über einen lokalen stdio-MCP-Server erweitert.
**Grund:** unterstützter Integrationspunkt; GUI-RPA wäre fragil und sicherheitswidrig.

## ADR-003 — Keine automatische Modellinstallation
**Entscheidung:** keine `ollama pull`-Aktion im Hintergrund.
**Grund:** große Downloads, Kosten/Last und irreversible Nutzerüberraschung; vorhandene Modelle werden live geprüft.

## ADR-004 — OpenClaw-Host und UI-Host getrennt
**Entscheidung:** Bridge ruft OpenClaw nur in der lokalen UI-Orchestrierung auf; bei OpenClaw-Host stellt sie nur Ollama-Tools bereit.
**Grund:** verhindert rekursive A→B→A-Aufrufe.

## ADR-005 — Laufdaten außerhalb des Repositories
**Entscheidung:** Runtime unter OS-Datenordner, pro Lauf temporäre Prompts, nur latest report.
**Grund:** Nutzeranforderung, Workspace darf nicht anwachsen; zugleich braucht die Anwendung lokale Diagnoseevidenz.
