from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable


SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}
SENSITIVE_SUFFIXES = (".pem", ".key", ".pfx", ".p12", ".kdb", ".secret")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(path, payload)


def expand_path(value: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(value)))).resolve()


def is_within(path: Path, roots: Iterable[Path]) -> bool:
    candidate = path.resolve()
    for root in roots:
        try:
            candidate.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def is_sensitive_path(path: Path) -> bool:
    name = path.name.lower()
    return name in SENSITIVE_NAMES or name.endswith(SENSITIVE_SUFFIXES)


def infer_mime(filename: str) -> str:
    known = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".json5": "application/json",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".py": "text/x-python",
        ".ps1": "text/plain",
        ".psm1": "text/plain",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".tsx": "text/typescript",
        ".jsx": "text/javascript",
        ".xml": "application/xml",
        ".csv": "text/csv",
        ".html": "text/html",
        ".css": "text/css",
        ".sh": "text/plain",
        ".toml": "application/toml",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    suffix = Path(filename).suffix.lower()
    return known.get(suffix) or mimetypes.guess_type(filename)[0] or "application/octet-stream"


def safe_filename(value: str) -> str:
    name = Path(value or "datei.bin").name
    name = re.sub(r"[^A-Za-z0-9._()\- äöüÄÖÜß]+", "_", name).strip(" .")
    return name[:180] or "datei.bin"
