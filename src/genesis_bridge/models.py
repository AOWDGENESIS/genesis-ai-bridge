from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResult:
    provider: str
    status: str
    model: str | None = None
    text: str = ""
    error: str | None = None
    duration_ms: int = 0
    parts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "model": self.model,
            "text": self.text,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "parts": self.parts,
            "metadata": self.metadata,
        }


@dataclass
class RunResult:
    run_id: str
    filename: str
    sha256: str
    size_bytes: int
    mime_type: str
    task: str
    status: str
    results: list[ProviderResult] = field(default_factory=list)
    synthesis: ProviderResult | None = None
    warnings: list[str] = field(default_factory=list)
    created_at: str = ""
    scope: str = "file"
    entry_count: int = 1
    total_bytes: int | None = None
    source_path: str | None = None
    program_name: str | None = None
    entries: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "filename": self.filename,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "task": self.task,
            "status": self.status,
            "results": [item.as_dict() for item in self.results],
            "synthesis": self.synthesis.as_dict() if self.synthesis else None,
            "warnings": self.warnings,
            "created_at": self.created_at,
            "scope": self.scope,
            "entry_count": self.entry_count,
            "total_bytes": self.total_bytes if self.total_bytes is not None else self.size_bytes,
            "source_path": self.source_path,
            "program_name": self.program_name,
            "entries": self.entries,
        }
