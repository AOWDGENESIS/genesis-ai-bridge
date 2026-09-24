from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from genesis_bridge.config import BridgeConfig, DEFAULTS
from genesis_bridge.paths import is_within
from genesis_bridge.shared import SharedArtifact


class CoreTests(unittest.TestCase):
    def test_artifact_hash_and_utf8(self) -> None:
        data = "ÄÖÜ ß\nzweite Zeile".encode("utf-8")
        artifact = SharedArtifact.from_bytes("beispiel.txt", data, 1000)
        self.assertEqual(artifact.sha256, "97df2985baf79607d038604eb66fad64f04fa348140262232c6f94d4cb081709")
        self.assertEqual(artifact.text, "ÄÖÜ ß\nzweite Zeile")

    def test_chunking_is_deterministic(self) -> None:
        artifact = SharedArtifact.from_bytes("x.txt", ("abc\n" * 5000).encode(), 100000)
        first = artifact.chunks(1000, 100000)
        second = artifact.chunks(1000, 100000)
        self.assertEqual(first, second)
        self.assertGreater(len(first), 1)
        self.assertEqual("".join(first), artifact.text)

    def test_path_containment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            inside = root / "inside.txt"
            outside = root.parent / f"{root.name}-outside.txt"
            self.assertTrue(is_within(inside, [root]))
            self.assertFalse(is_within(outside, [root]))

    def test_default_config_loads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = BridgeConfig.load(path)
            self.assertEqual(config.ollama_model, DEFAULTS["ollama_model"])
            self.assertEqual(config.max_file_bytes, DEFAULTS["max_file_bytes"])


if __name__ == "__main__":
    unittest.main()
