from __future__ import annotations

import hashlib
import io
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable

from .config import BridgeConfig
from .paths import is_sensitive_path
from .shared import SharedArtifact


@dataclass(frozen=True)
class BundleEntry:
    relative_path: str
    data: bytes
    artifact: SharedArtifact
    source_kind: str = "file"

    def as_dict(self) -> dict:
        return {
            "path": self.relative_path,
            "size_bytes": len(self.data),
            "sha256": self.artifact.sha256,
            "mime_type": self.artifact.mime_type,
            "text": self.artifact.text is not None,
            "source_kind": self.source_kind,
        }


@dataclass
class InspectionBundle:
    name: str
    kind: str
    entries: list[BundleEntry]
    total_bytes: int
    sha256: str
    source_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    source_bytes: bytes | None = None

    @property
    def mime_type(self) -> str:
        return {
            "zip": "application/zip",
            "directory": "inode/directory",
            "files": "application/octet-stream",
        }.get(self.kind, "application/octet-stream")

    def manifest_text(self, preview_chars: int = 500) -> str:
        lines = [
            f"Bundle: {self.name}",
            f"Typ: {self.kind}",
            f"SHA-256 des deterministischen Inhaltsmanifests: {self.sha256}",
            f"Dateien: {len(self.entries)}",
            "",
        ]
        for entry in self.entries:
            preview = ""
            if entry.artifact.text is not None:
                preview = entry.artifact.text[:preview_chars].replace("\x00", "")
                if len(entry.artifact.text) > preview_chars:
                    preview += " [...]"
            lines.append(
                f"- {entry.relative_path} | {len(entry.data)} Bytes | {entry.artifact.sha256} | {entry.artifact.mime_type}"
            )
            if preview:
                lines.append(f"  Vorschau: {preview.replace(chr(10), ' ')}")
        if self.warnings:
            lines.extend(["", "Warnungen:", *[f"- {item}" for item in self.warnings]])
        return "\n".join(lines)

    def manifest_artifact(self, max_bytes: int) -> SharedArtifact:
        data = self.manifest_text().encode("utf-8")
        return SharedArtifact.from_bytes(f"{self.name}-MANIFEST.txt", data[:max_bytes], max_bytes)


def _manifest_hash(entries: Iterable[BundleEntry]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item.relative_path):
        digest.update(entry.relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry.artifact.sha256.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(len(entry.data)).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _validate_relative(name: str) -> str:
    raw = name.replace("\\", "/")
    path = PurePosixPath(raw)
    drive_path = len(raw) >= 2 and raw[0].isalpha() and raw[1] == ":"
    if "\x00" in raw or path.is_absolute() or drive_path or ".." in path.parts or any(part == "" for part in path.parts):
        raise ValueError(f"Unsicherer relativer Pfad im Bundle: {name}")
    cleaned = "/".join(part for part in path.parts if part not in {"."})
    if not cleaned or cleaned.startswith("/"):
        raise ValueError(f"Ungültiger Bundle-Pfad: {name}")
    return cleaned


def _is_zip_name(name: str) -> bool:
    return Path(name).suffix.lower() in {".zip", ".jar", ".whl", ".apk", ".ipa"}


def _looks_like_nested_zip(name: str, data: bytes) -> bool:
    if _is_zip_name(name):
        return True
    try:
        return zipfile.is_zipfile(io.BytesIO(data))
    except (OSError, ValueError):
        return False


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    # Unix symlink type bits in external_attr. Never materialize or follow them.
    return ((info.external_attr >> 16) & 0o170000) == 0o120000


def _entry(relative_path: str, data: bytes, config: BridgeConfig, source_kind: str) -> BundleEntry:
    if len(data) > config.max_file_bytes:
        raise ValueError(f"Datei im Bundle ist zu groß: {relative_path} ({len(data)} Bytes).")
    artifact = SharedArtifact.from_bytes(relative_path, data, config.max_file_bytes)
    return BundleEntry(relative_path, data, artifact, source_kind)


def from_path(path: Path, config: BridgeConfig) -> InspectionBundle:
    original = path.expanduser()
    if original.is_symlink():
        raise ValueError("Symbolische Links werden als Quelle aus Sicherheitsgründen nicht verfolgt.")
    candidate = original.resolve()
    if is_sensitive_path(candidate):
        raise ValueError("Sensible Schlüssel-/Credential-Dateien werden nicht automatisch eingelesen.")
    if candidate.is_dir():
        return from_directory(candidate, config)
    if candidate.suffix.lower() == ".zip" or zipfile.is_zipfile(candidate):
        if candidate.stat().st_size > config.max_bundle_bytes:
            raise ValueError("Das ZIP-Archiv überschreitet das Bundle-Größenlimit.")
        return from_zip_bytes(candidate.name, candidate.read_bytes(), config, candidate)
    return from_file(candidate, config)


def from_file(path: Path, config: BridgeConfig) -> InspectionBundle:
    if path.is_symlink():
        raise ValueError("Symbolische Links werden als Quelle aus Sicherheitsgründen nicht verfolgt.")
    if is_sensitive_path(path):
        raise ValueError("Sensible Schlüssel-/Credential-Dateien werden nicht automatisch eingelesen.")
    data = path.read_bytes()
    entry = _entry(path.name, data, config, "file")
    return InspectionBundle(path.name, "files", [entry], len(data), _manifest_hash([entry]), path, [], data)


def from_directory(path: Path, config: BridgeConfig) -> InspectionBundle:
    entries: list[BundleEntry] = []
    warnings: list[str] = []
    total = 0
    for root, directories, filenames in os.walk(path, topdown=True, followlinks=False):
        root_path = Path(root)
        safe_directories: list[str] = []
        for directory in sorted(directories):
            candidate = root_path / directory
            if candidate.is_symlink():
                warnings.append(f"Symlink-Ordner übersprungen: {candidate.relative_to(path)}")
            else:
                safe_directories.append(directory)
        directories[:] = safe_directories
        for filename in sorted(filenames):
            item = root_path / filename
            relative_path = item.relative_to(path)
            if item.is_symlink():
                warnings.append(f"Symlink übersprungen: {relative_path}")
                continue
            if not item.is_file():
                continue
            if is_sensitive_path(item):
                warnings.append(f"Sensible Datei übersprungen: {relative_path}")
                continue
            relative = relative_path.as_posix()
            data = item.read_bytes()
            total += len(data)
            if total > config.max_bundle_bytes:
                raise ValueError("Das Verzeichnis überschreitet das Bundle-Größenlimit.")
            entries.append(_entry(relative, data, config, "directory"))
            if len(entries) > config.max_bundle_entries:
                raise ValueError("Das Verzeichnis enthält mehr Dateien als erlaubt.")
    return InspectionBundle(path.name, "directory", entries, total, _manifest_hash(entries), path, warnings)


def from_zip_bytes(
    name: str,
    data: bytes,
    config: BridgeConfig,
    source_path: Path | None = None,
    depth: int = 0,
) -> InspectionBundle:
    if len(data) > config.max_bundle_bytes:
        raise ValueError("Das ZIP-Archiv überschreitet das Bundle-Größenlimit.")
    entries: list[BundleEntry] = []
    warnings: list[str] = []
    total = 0

    def read_zip(raw: bytes, prefix: str, current_depth: int) -> None:
        nonlocal total
        try:
            archive = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Ungültiges ZIP-Archiv: {name}") from exc
        with archive:
            infos = archive.infolist()
            if len(entries) + len(infos) > config.max_bundle_entries:
                raise ValueError("Das Archiv enthält mehr Einträge als erlaubt.")
            for info in infos:
                if info.is_dir():
                    continue
                if _is_symlink(info):
                    warnings.append(f"Symlink im Archiv übersprungen: {prefix}{info.filename}")
                    continue
                relative = _validate_relative(f"{prefix}{info.filename}")
                if info.file_size > config.max_file_bytes:
                    raise ValueError(f"Archivdatei ist zu groß: {relative}")
                if info.compress_size == 0 and info.file_size > config.max_file_bytes:
                    raise ValueError(f"Verdächtiges Archivverhältnis: {relative}")
                raw_entry = archive.read(info)
                if len(raw_entry) != info.file_size:
                    raise ValueError(f"Archivdatei konnte nicht vollständig gelesen werden: {relative}")
                total += len(raw_entry)
                if total > config.max_bundle_bytes:
                    raise ValueError("Das entpackte Archiv überschreitet das Bundle-Größenlimit.")
                nested_archive = _looks_like_nested_zip(relative, raw_entry)
                if nested_archive and current_depth < config.max_archive_depth:
                    try:
                        read_zip(raw_entry, relative + "/", current_depth + 1)
                        continue
                    except ValueError:
                        raise
                    except Exception:
                        warnings.append(f"Verschachteltes Archiv nicht lesbar: {relative}")
                elif nested_archive:
                    warnings.append(f"Archiv-Tiefenlimit erreicht; nicht weiter entpackt: {relative}")
                entries.append(_entry(relative, raw_entry, config, "zip"))

    read_zip(data, "", depth)
    return InspectionBundle(name, "zip", entries, total, _manifest_hash(entries), source_path, warnings, data)


def from_uploads(name: str, uploads: list[tuple[str, bytes]], config: BridgeConfig) -> InspectionBundle:
    if len(uploads) == 1 and _looks_like_nested_zip(uploads[0][0], uploads[0][1]):
        return from_zip_bytes(uploads[0][0], uploads[0][1], config)
    entries: list[BundleEntry] = []
    total = 0
    warnings: list[str] = []
    for relative, data in uploads:
        clean = _validate_relative(relative.replace("\\", "/"))
        if is_sensitive_path(Path(clean)):
            warnings.append(f"Sensible Datei übersprungen: {clean}")
            continue
        total += len(data)
        if total > config.max_bundle_bytes:
            raise ValueError("Die Upload-Auswahl überschreitet das Bundle-Größenlimit.")
        entries.append(_entry(clean, data, config, "upload"))
    if len(entries) > config.max_bundle_entries:
        raise ValueError("Die Upload-Auswahl enthält mehr Dateien als erlaubt.")
    return InspectionBundle(name, "files", entries, total, _manifest_hash(entries), None, warnings)


def bundle_to_json(bundle: InspectionBundle) -> dict:
    return {
        "name": bundle.name,
        "kind": bundle.kind,
        "entry_count": len(bundle.entries),
        "total_bytes": bundle.total_bytes,
        "sha256": bundle.sha256,
        "source_path": str(bundle.source_path) if bundle.source_path else None,
        "warnings": bundle.warnings,
        "entries": [entry.as_dict() for entry in bundle.entries],
    }
