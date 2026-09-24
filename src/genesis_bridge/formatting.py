from __future__ import annotations

from typing import Any


def markdown_report(value: dict[str, Any]) -> str:
    lines = [
        f"# Genesis AI Bridge — Lauf {value.get('run_id', '')}",
        "",
        f"- **Status:** {value.get('status', '')}",
        f"- **Umfang:** `{value.get('scope', 'file')}` · {value.get('entry_count', 1)} Eintrag/Einträge",
        f"- **Quelle:** `{value.get('filename', '')}`",
        f"- **Lokaler Quellpfad:** `{value.get('source_path') or 'nicht übermittelt'}`",
        f"- **SHA-256 / Manifest:** `{value.get('sha256', '')}`",
        f"- **Größe:** {value.get('size_bytes', 0)} Bytes · Gesamtinhalt: {value.get('total_bytes', value.get('size_bytes', 0))} Bytes",
        f"- **MIME:** `{value.get('mime_type', '')}`",
        f"- **Aufgabe:** {value.get('task', '')}",
        "",
    ]
    entries = value.get("entries") or []
    if entries:
        lines.extend(["## Bundle-Einträge", ""])
        for entry in entries:
            lines.append(
                f"- `{entry.get('path', '')}` — {entry.get('size_bytes', 0)} Bytes — "
                f"`{entry.get('sha256', '')}` — {entry.get('status', 'not_tested')}"
            )
        lines.append("")
    lines.extend(["## Ergebnisse", ""])
    for result in value.get("results", []):
        lines.extend([
            f"### {result.get('provider', '')} — {result.get('status', '')}",
            f"Modell: `{result.get('model') or '—'}` · Dauer: {result.get('duration_ms', 0)} ms · Teile: {result.get('parts', 0)}",
            "",
            result.get("text") or result.get("error") or "Keine Ausgabe.",
            "",
        ])
    synthesis = value.get("synthesis")
    if synthesis:
        lines.extend([
            "## Gemeinsame Zusammenfassung",
            "",
            synthesis.get("text") or synthesis.get("error") or "Keine Synthese.",
            "",
        ])
    warnings = value.get("warnings") or []
    if warnings:
        lines.extend(["## Warnungen", "", *[f"- {item}" for item in warnings], ""])
    return "\n".join(lines).rstrip() + "\n"
