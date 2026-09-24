from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from .config import BridgeConfig
from .paths import infer_mime, safe_filename, sha256_bytes


TEXT_MIME_PREFIXES = ("text/", "application/json", "application/xml", "application/toml")
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".json5", ".yaml", ".yml", ".py", ".ps1", ".psm1",
    ".js", ".ts", ".tsx", ".jsx", ".xml", ".csv", ".html", ".css", ".sh", ".toml",
    ".ini", ".cfg", ".conf", ".log", ".sql", ".java", ".cs", ".cpp", ".h", ".hpp",
}
IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@dataclass(frozen=True)
class SharedArtifact:
    filename: str
    data: bytes
    sha256: str
    mime_type: str
    text: str | None

    @classmethod
    def from_bytes(cls, filename: str, data: bytes, max_bytes: int) -> "SharedArtifact":
        if len(data) > max_bytes:
            raise ValueError(f"Datei ist zu groß: {len(data)} Bytes; erlaubt sind {max_bytes}.")
        clean_name = safe_filename(filename)
        mime_type = infer_mime(clean_name)
        text = decode_text(clean_name, mime_type, data)
        return cls(clean_name, data, sha256_bytes(data), mime_type, text)

    @classmethod
    def from_path(cls, path: Path, max_bytes: int) -> "SharedArtifact":
        if not path.is_file():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")
        size = path.stat().st_size
        if size > max_bytes:
            raise ValueError(f"Datei ist zu groß: {size} Bytes; erlaubt sind {max_bytes}.")
        return cls.from_bytes(path.name, path.read_bytes(), max_bytes)

    @classmethod
    def from_base64(cls, filename: str, value: str, max_bytes: int) -> "SharedArtifact":
        try:
            data = base64.b64decode(value, validate=True)
        except Exception as exc:  # pragma: no cover - exact base64 error differs by Python
            raise ValueError("content_base64 ist ungültig.") from exc
        return cls.from_bytes(filename, data, max_bytes)

    @property
    def is_image(self) -> bool:
        return self.mime_type in IMAGE_MIMES

    @property
    def is_text(self) -> bool:
        return self.text is not None

    def chunks(self, chunk_chars: int, max_input_chars: int) -> list[str]:
        if self.text is None:
            return []
        value = self.text
        if len(value) > max_input_chars:
            value = value[: max_input_chars // 2] + "\n\n[... Mitte wegen Kontextlimit ausgelassen ...]\n\n" + value[-max_input_chars // 2 :]
        if len(value) <= chunk_chars:
            return [value]
        chunks: list[str] = []
        start = 0
        while start < len(value):
            end = min(len(value), start + chunk_chars)
            if end < len(value):
                boundary = max(value.rfind("\n", start, end), value.rfind(" ", start, end))
                if boundary > start + chunk_chars // 2:
                    end = boundary
            chunks.append(value[start:end])
            start = end
        return chunks

    def content_for_prompt(self, max_chars: int) -> str:
        if self.text is not None:
            if len(self.text) <= max_chars:
                return self.text
            return self.text[: max_chars // 2] + "\n[... gekürzt ...]\n" + self.text[-max_chars // 2 :]
        if self.is_image:
            return "[Binärbild: Der Vision-Inhalt wird separat als Bild an Ollama übergeben.]"
        return "[Binärdatei: Es wurde nur Metadatenanalyse durchgeführt.]"


def decode_text(filename: str, mime_type: str, data: bytes) -> str | None:
    suffix = Path(filename).suffix.lower()
    if not (mime_type.startswith(TEXT_MIME_PREFIXES) or suffix in TEXT_SUFFIXES):
        return None
    encodings = ["utf-8-sig"]
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        encodings = ["utf-16"]
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
