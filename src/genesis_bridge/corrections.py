from __future__ import annotations

import base64
import io
import json
import re
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .bundle import InspectionBundle, _is_symlink, _looks_like_nested_zip
from .config import BridgeConfig
from .paths import atomic_write_bytes, atomic_write_json, is_sensitive_path, sha256_bytes


@dataclass(frozen=True)
class CorrectionChange:
    path: str
    action: str
    content: bytes
    reason: str = ""

    def as_dict(self, include_content: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "path": self.path,
            "action": self.action,
            "content_sha256": sha256_bytes(self.content),
            "content_bytes": len(self.content),
            "reason": self.reason,
        }
        if include_content:
            try:
                value["content"] = self.content.decode("utf-8")
                value["encoding"] = "utf-8"
            except UnicodeDecodeError:
                value["content_base64"] = base64.b64encode(self.content).decode("ascii")
                value["encoding"] = "base64"
        return value


@dataclass
class CorrectionProposal:
    proposal_id: str
    run_id: str
    bundle_name: str
    bundle_sha256: str
    source_path: str | None
    program_name: str
    target_parent: str
    summary: str
    changes: list[CorrectionChange] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    status: str = "proposed"
    created_at: str = ""
    applied_at: str | None = None
    target_path: str | None = None

    def as_dict(self, include_content: bool = True) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "run_id": self.run_id,
            "bundle_name": self.bundle_name,
            "bundle_sha256": self.bundle_sha256,
            "source_path": self.source_path,
            "program_name": self.program_name,
            "target_parent": self.target_parent,
            "target_path": self.target_path,
            "summary": self.summary,
            "changes": [item.as_dict(include_content) for item in self.changes],
            "warnings": self.warnings,
            "status": self.status,
            "created_at": self.created_at,
            "applied_at": self.applied_at,
        }


def _safe_relative(value: str) -> str:
    raw = str(value or "").replace("\\", "/")
    path = PurePosixPath(raw)
    drive_path = len(raw) >= 2 and raw[0].isalpha() and raw[1] == ":"
    if "\x00" in raw or path.is_absolute() or drive_path or not path.parts or ".." in path.parts or any(part == "" for part in path.parts):
        raise ValueError(f"Unsicherer Korrekturpfad: {value}")
    cleaned = "/".join(part for part in path.parts if part != ".")
    if not cleaned or cleaned.startswith("/"):
        raise ValueError(f"Ungültiger Korrekturpfad: {value}")
    return cleaned


def safe_program_name(value: str | None, fallback: str) -> str:
    candidate = (value or fallback or "Programm").strip()
    candidate = re.sub(r"[^A-Za-z0-9._()\- äöüÄÖÜß]+", "_", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip(" .")
    return (candidate[:100] or "Programm")


def _decode_change(item: dict[str, Any]) -> bytes:
    if "content_base64" in item:
        try:
            return base64.b64decode(str(item["content_base64"]), validate=True)
        except Exception as exc:  # pragma: no cover - exact base64 error differs by Python
            raise ValueError("content_base64 einer Korrektur ist ungültig.") from exc
    content = item.get("content", "")
    if not isinstance(content, str):
        raise ValueError("Der Korrekturinhalt muss Text oder content_base64 sein.")
    return content.encode("utf-8")


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_correction_response(
    raw: str,
    bundle: InspectionBundle,
    run_id: str,
    program_name: str | None,
    target_parent: Path,
    max_changes: int,
    max_content_bytes: int = 32 * 1024 * 1024,
) -> CorrectionProposal:
    warnings: list[str] = []
    try:
        value = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError as exc:
        return CorrectionProposal(
            proposal_id=uuid.uuid4().hex,
            run_id=run_id,
            bundle_name=bundle.name,
            bundle_sha256=bundle.sha256,
            source_path=str(bundle.source_path) if bundle.source_path else None,
            program_name=safe_program_name(program_name, Path(bundle.name).stem),
            target_parent=str(target_parent),
            summary="Es konnte kein maschinenlesbarer Korrekturvorschlag erzeugt werden.",
            warnings=[f"Provider-Antwort war kein gültiges JSON: {exc}"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    if not isinstance(value, dict):
        value = {}
        warnings.append("Provider-Antwort war kein JSON-Objekt.")
    allowed = {entry.relative_path for entry in bundle.entries}
    changes: list[CorrectionChange] = []
    seen_paths: set[str] = set()
    raw_changes = value.get("files", [])
    if not isinstance(raw_changes, list):
        warnings.append("Das Feld files war keine Liste; es wurden keine Korrekturen übernommen.")
        raw_changes = []
    if len(raw_changes) > max_changes:
        warnings.append(f"Nur die ersten {max_changes} Korrekturvorschläge wurden berücksichtigt.")
    for raw_item in raw_changes[:max_changes]:
        if not isinstance(raw_item, dict):
            warnings.append("Ein Korrekturvorschlag war kein Objekt und wurde verworfen.")
            continue
        try:
            relative = _safe_relative(str(raw_item.get("path", "")))
            if relative not in allowed:
                raise ValueError("Pfad gehört nicht zu den geprüften bestehenden Dateien.")
            if relative in seen_paths:
                raise ValueError("Ein Pfad wurde mehrfach vorgeschlagen.")
            seen_paths.add(relative)
            if is_sensitive_path(Path(relative)):
                raise ValueError("Sensible Dateien dürfen nicht korrigiert werden.")
            action = str(raw_item.get("action", "replace")).lower()
            if action != "replace":
                raise ValueError("Nur action=replace ist erlaubt.")
            content = _decode_change(raw_item)
            original = next(entry for entry in bundle.entries if entry.relative_path == relative)
            if len(content) > min(max(len(original.data) * 10 + 1_000_000, 1_000_000), max_content_bytes):
                raise ValueError("Der vorgeschlagene Inhalt ist unverhältnismäßig groß.")
            changes.append(CorrectionChange(relative, action, content, str(raw_item.get("reason") or "")))
        except (TypeError, ValueError) as exc:
            warnings.append(f"Korrektur verworfen: {exc}")
    provider_warnings = value.get("warnings") or []
    if isinstance(provider_warnings, list):
        warnings.extend(str(item) for item in provider_warnings[:50])
    else:
        warnings.append("Provider-Warnungen waren keine Liste.")
    return CorrectionProposal(
        proposal_id=uuid.uuid4().hex,
        run_id=run_id,
        bundle_name=bundle.name,
        bundle_sha256=bundle.sha256,
        source_path=str(bundle.source_path) if bundle.source_path else None,
        program_name=safe_program_name(program_name, Path(bundle.name).stem),
        target_parent=str(target_parent),
        summary=str(value.get("summary") or ("Keine sichere Korrektur vorgeschlagen." if not changes else f"{len(changes)} sichere Korrektur(en) vorgeschlagen.")),
        changes=changes,
        warnings=warnings,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def correction_parent(bundle: InspectionBundle, program_name: str | None, config: BridgeConfig) -> tuple[Path, str, str | None]:
    program = safe_program_name(program_name, Path(bundle.name).stem)
    if bundle.source_path:
        source = bundle.source_path.expanduser().resolve()
        parent = source.parent
        source_value = str(source)
    else:
        # A browser upload has no trustworthy local source location. Keep it visibly external.
        parent = config.data_dir
        source_value = None
    return parent / "Korrekturen" / program, program, source_value


def _reject_symlink_components(path: Path) -> None:
    absolute = path.expanduser().absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"Symlink im Korrekturpfad wird nicht verwendet: {current}")


def _target_path(root: Path, relative: str) -> Path:
    clean = _safe_relative(relative)
    target = (root / Path(*clean.split("/"))).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Korrekturziel verlässt den Zielordner.") from exc
    return target


def _write_tree(root: Path, payloads: dict[str, bytes]) -> None:
    for relative, data in payloads.items():
        target = _target_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.is_symlink():
            raise ValueError(f"Symlink im Korrekturziel wird nicht überschrieben: {relative}")
        atomic_write_bytes(target, data)


def _rewrite_zip(raw: bytes, changes: dict[str, CorrectionChange], prefix: str = "", depth: int = 0) -> bytes:
    if depth > 8:
        raise ValueError("Verschachteltes Archiv überschreitet das Korrekturlimit.")
    source = zipfile.ZipFile(io.BytesIO(raw))
    output = io.BytesIO()
    with source, zipfile.ZipFile(output, "w") as destination:
        for info in source.infolist():
            if _is_symlink(info):
                continue
            if info.is_dir():
                destination.writestr(info, b"")
                continue
            relative = _safe_relative(f"{prefix}{info.filename}")
            payload = source.read(info)
            direct = changes.get(relative)
            if direct is not None:
                payload = direct.content
            elif any(path.startswith(relative + "/") for path in changes):
                if _looks_like_nested_zip(relative, payload):
                    payload = _rewrite_zip(payload, changes, relative + "/", depth + 1)
            destination.writestr(info, payload)
    return output.getvalue()


def _zip_payload(bundle: InspectionBundle, changes: dict[str, CorrectionChange]) -> bytes:
    raw = bundle.source_bytes
    if raw is None and bundle.source_path and bundle.source_path.is_file():
        raw = bundle.source_path.read_bytes()
    if raw is None:
        raise ValueError("Für die korrigierte ZIP-Datei fehlen die ursprünglichen Archivbytes.")
    return _rewrite_zip(raw, changes)


class CorrectionManager:
    def __init__(self, config: BridgeConfig) -> None:
        self.config = config
        self.root = config.data_dir / "proposals"
        self.root.mkdir(parents=True, exist_ok=True)

    def save_proposal(self, proposal: CorrectionProposal) -> None:
        atomic_write_json(self.root / proposal.proposal_id / "Korrekturvorschlag.json", proposal.as_dict())

    def apply(self, proposal: CorrectionProposal, bundle: InspectionBundle) -> dict[str, Any]:
        if proposal.status != "proposed":
            raise ValueError(f"Korrekturvorschlag hat bereits den Status {proposal.status}.")
        if not proposal.changes:
            raise ValueError("Es gibt keine sichere Korrektur anzuwenden.")
        if bundle.sha256 != proposal.bundle_sha256:
            raise ValueError("Die Ausgangsdatei bzw. das Bundle hat sich seit der Analyse verändert; Korrektur abgebrochen.")
        raw_correction_root = Path(proposal.target_parent).expanduser()
        _reject_symlink_components(raw_correction_root)
        correction_root = raw_correction_root.resolve()
        if bundle.source_path:
            source = bundle.source_path.expanduser().resolve()
            try:
                correction_root.relative_to(source if source.is_dir() else source.parent)
            except ValueError:
                pass
            else:
                if source.is_dir():
                    raise ValueError("Das Korrekturziel läge innerhalb der Quelle; Originalschutz bricht den Lauf ab.")
                if correction_root == source.parent:
                    raise ValueError("Das Korrekturziel ist nicht von der Quelldatei getrennt.")
        correction_root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = correction_root / timestamp
        counter = 2
        while target.exists():
            target = correction_root / f"{timestamp}-{counter}"
            counter += 1
        target.mkdir(parents=True, exist_ok=False)
        changes = {item.path: item for item in proposal.changes}
        if bundle.kind == "zip":
            corrected_zip = _zip_payload(bundle, changes)
            stem = Path(bundle.name).stem or "archiv"
            zip_name = f"{stem}.korrigiert.zip"
            atomic_write_bytes(target / zip_name, corrected_zip)
            # A readable copy of the inspected hierarchy is useful without claiming it is the source archive.
            hierarchy = target / "Inhalt"
            payloads = {entry.relative_path: changes.get(entry.relative_path, CorrectionChange(entry.relative_path, "replace", entry.data)).content for entry in bundle.entries if "/" not in entry.relative_path or not (Path(entry.relative_path).suffix.lower() == ".zip")}
            _write_tree(hierarchy, payloads)
        else:
            payloads = {entry.relative_path: entry.data for entry in bundle.entries}
            for item in proposal.changes:
                payloads[item.path] = item.content
            _write_tree(target, payloads)
        proposal.status = "applied"
        proposal.applied_at = datetime.now(timezone.utc).isoformat()
        proposal.target_path = str(target)
        plan = proposal.as_dict()
        plan["source_manifest_sha256"] = bundle.sha256
        plan["source_entry_hashes"] = {entry.relative_path: entry.artifact.sha256 for entry in bundle.entries}
        plan["changes_applied"] = [
            {
                **item.as_dict(include_content=False),
                "old_sha256": next((entry.artifact.sha256 for entry in bundle.entries if entry.relative_path == item.path), None),
                "new_sha256": sha256_bytes(item.content),
            }
            for item in proposal.changes
        ]
        atomic_write_json(target / "Korrekturplan.json", plan)
        atomic_write_json(self.root / proposal.proposal_id / "Korrekturvorschlag.json", proposal.as_dict())
        return {
            "ok": True,
            "status": proposal.status,
            "proposal": proposal.as_dict(include_content=False),
            "target_path": str(target),
            "plan_path": str(target / "Korrekturplan.json"),
            "changes": plan["changes_applied"],
            "warnings": proposal.warnings,
        }
