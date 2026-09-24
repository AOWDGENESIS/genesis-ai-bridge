from __future__ import annotations

import shutil
from pathlib import Path


def clear_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for item in path.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)


def prune_tree(path: Path, max_bytes: int = 20 * 1024 * 1024) -> None:
    if not path.exists():
        return
    files = [item for item in path.rglob("*") if item.is_file()]
    total = sum(item.stat().st_size for item in files)
    if total <= max_bytes:
        return
    for item in sorted(files, key=lambda item: item.stat().st_mtime):
        try:
            total -= item.stat().st_size
            item.unlink()
        except OSError:
            pass
        if total <= max_bytes:
            break
