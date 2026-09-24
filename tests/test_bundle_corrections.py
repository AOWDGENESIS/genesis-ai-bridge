from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from genesis_bridge.bundle import from_directory, from_uploads, from_zip_bytes
from genesis_bridge.config import BridgeConfig
from genesis_bridge.corrections import CorrectionManager, correction_parent, parse_correction_response
from genesis_bridge.ollama import OllamaResponse
from genesis_bridge.orchestrator import BridgeOrchestrator


class BundleAndCorrectionTests(unittest.TestCase):
    def config(self, directory: str) -> BridgeConfig:
        config = BridgeConfig.load(Path(directory) / "config.json")
        config.data_dir = Path(directory) / "state"
        config.max_bundle_entries = 100
        return config

    @staticmethod
    def zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for name, data in entries:
                archive.writestr(name, data)
        return output.getvalue()

    def test_zip_and_nested_zip_are_fully_flattened(self) -> None:
        inner = self.zip_bytes([("nested/file.txt", b"inside")])
        outer = self.zip_bytes([("root.txt", b"root"), ("inner.zip", inner)])
        with tempfile.TemporaryDirectory() as directory:
            bundle = from_uploads("sample.zip", [("sample.zip", outer)], self.config(directory))
        paths = {entry.relative_path for entry in bundle.entries}
        self.assertEqual(paths, {"root.txt", "inner.zip/nested/file.txt"})
        self.assertEqual(bundle.entries[0].source_kind, "zip")
        self.assertEqual(bundle.total_bytes, len(outer) * 0 + len(b"root") + len(inner) + len(b"inside"))

    def test_zip_traversal_and_drive_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(directory)
            for name in ("../evil.txt", "C:/evil.txt", "\\\\server\\evil.txt"):
                with self.subTest(name=name):
                    raw = self.zip_bytes([(name, b"x")])
                    with self.assertRaises(ValueError):
                        from_zip_bytes("bad.zip", raw, config)

    def test_directory_is_recursive_and_skips_sensitive_and_symlink_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            (root / "one" / "two").mkdir(parents=True)
            (root / "one" / "two" / "file.txt").write_text("ok", encoding="utf-8")
            (root / ".env").write_text("SECRET=do-not-read", encoding="utf-8")
            try:
                (root / "link.txt").symlink_to(root / "one" / "two" / "file.txt")
            except (OSError, NotImplementedError):
                pass
            bundle = from_directory(root, self.config(directory))
            self.assertEqual([entry.relative_path for entry in bundle.entries], ["one/two/file.txt"])
            self.assertTrue(any(".env" in warning for warning in bundle.warnings))

    def test_explicit_correction_creates_new_tree_and_keeps_original(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "project"
            (source / "sub").mkdir(parents=True)
            (source / "sub" / "a.txt").write_text("old", encoding="utf-8")
            bundle = from_directory(source, self.config(directory))
            parent, _, _ = correction_parent(bundle, "Familien AI", self.config(directory))
            proposal = parse_correction_response(
                '{"summary":"sicher","files":[{"path":"sub/a.txt","action":"replace","content":"new","reason":"test"}]}',
                bundle,
                "run-1",
                "Familien AI",
                parent,
                10,
            )
            result = CorrectionManager(self.config(directory)).apply(proposal, bundle)
            target = Path(result["target_path"])
            self.assertEqual((target / "sub" / "a.txt").read_text(encoding="utf-8"), "new")
            self.assertEqual((source / "sub" / "a.txt").read_text(encoding="utf-8"), "old")
            self.assertTrue((target / "Korrekturplan.json").exists())
            self.assertEqual(result["changes"][0]["old_sha256"], bundle.entries[0].artifact.sha256)

    def test_orchestrator_entry_results_and_confirmation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(directory)
            orchestrator = BridgeOrchestrator(config)
            orchestrator.ollama.analyze_artifact = lambda artifact, prompt, model=None: OllamaResponse("Analyse", "fake", {}, 1)
            orchestrator.ollama.chat = lambda prompt, model=None, image_base64=None: OllamaResponse(
                '{"summary":"sicher","files":[{"path":"a.txt","action":"replace","content":"new"}]}',
                "fake",
                {},
                1,
            )
            result = orchestrator.run_uploads([("a.txt", b"old")], "Prüfe", ["ollama"], "Upload", "Familien AI")
            self.assertEqual(result.status, "complete")
            self.assertEqual(result.entry_count, 1)
            self.assertEqual(result.entries[0]["path"], "a.txt")
            proposal = orchestrator.propose_corrections(result.run_id)
            with self.assertRaises(ValueError):
                orchestrator.apply_corrections(proposal.proposal_id, False)
            applied = orchestrator.apply_corrections(proposal.proposal_id, True)
            self.assertEqual(Path(applied["target_path"]).joinpath("a.txt").read_text(encoding="utf-8"), "new")

    def test_zip_correction_writes_corrected_zip_and_external_upload_warning(self) -> None:
        raw = self.zip_bytes([("a.txt", b"old")])
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(directory)
            bundle = from_uploads("sample.zip", [("sample.zip", raw)], config)
            parent, _, source = correction_parent(bundle, "Familien AI", config)
            self.assertIsNone(source)
            proposal = parse_correction_response(
                '{"files":[{"path":"a.txt","action":"replace","content":"new"}]}',
                bundle,
                "run-zip",
                "Familien AI",
                parent,
                10,
            )
            result = CorrectionManager(config).apply(proposal, bundle)
            corrected = Path(result["target_path"]) / "sample.korrigiert.zip"
            with zipfile.ZipFile(corrected) as archive:
                self.assertEqual(archive.read("a.txt"), b"new")
            self.assertFalse((Path(directory) / "sample.zip").exists())


if __name__ == "__main__":
    unittest.main()
