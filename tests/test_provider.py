from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from genesis_bridge.config import BridgeConfig
from genesis_bridge.doctor import Doctor
from genesis_bridge.ollama import OllamaClient, normalized_base_url
from genesis_bridge.orchestrator import BridgeOrchestrator


class FakeOllamaHandler(BaseHTTPRequestHandler):
    def _write(self, value: object, status: int = 200) -> None:
        data = json.dumps(value, ensure_ascii=False).encode("utf-8") if not isinstance(value, str) else value.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._write("Ollama is running")
        elif self.path == "/api/tags":
            self._write({"models": [{"name": "qwen3:test", "size": 5000000000, "details": {"parameter_size": "8B"}}]})
        elif self.path == "/api/version":
            self._write({"version": "test"})
        else:
            self._write({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        if self.path == "/api/show":
            self._write({"capabilities": ["completion", "tools"], "model_info": {"qwen3.context_length": 32768}, "details": {"parameter_size": "8B"}})
        elif self.path == "/api/chat":
            self._write({"model": body["model"], "message": {"role": "assistant", "content": "FAKE PASS: Hash im Prompt erkannt."}, "done": True})
        else:
            self._write({"error": "not found"}, 404)

    def log_message(self, fmt: str, *args: object) -> None:
        return


class ProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def make_config(self, directory: str) -> BridgeConfig:
        path = Path(directory) / "config.json"
        config = BridgeConfig.load(path)
        config.data_dir = Path(directory) / "data"
        config.ollama_base_url = self.url
        return config

    def test_loopback_normalization(self) -> None:
        self.assertEqual(normalized_base_url("http://0.0.0.0:11434"), "http://127.0.0.1:11434")
        self.assertEqual(normalized_base_url("http://localhost:11434/"), "http://127.0.0.1:11434")

    def test_ollama_discovery_and_chat(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = OllamaClient(self.make_config(directory))
            self.assertTrue(client.health()["ok"])
            model = client.choose_model()
            self.assertEqual(model.name, "qwen3:test")
            response = client.chat("Hallo")
            self.assertIn("FAKE PASS", response.text)

    def test_orchestrator_writes_only_latest_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory)
            config.chunk_chars = 40
            config.max_input_chars = 200
            result = BridgeOrchestrator(config).run_bytes("übung.txt", "ÄÖÜ\n".encode(), "Prüfe Hash", ["ollama"])
            self.assertEqual(result.status, "complete")
            self.assertTrue(config.latest_json.exists())
            self.assertTrue(config.latest_markdown.exists())
            self.assertEqual(result.sha256, "31e8b00197499595bfed0b9dda72fa649d4f13edc8e8ac3894f5fff466f434d6")
            runs = [item for item in (config.data_dir / "runs").iterdir() if item.name != ".gitkeep"]
            self.assertEqual(runs, [])

    def test_doctor_loop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_config(directory)
            result = Doctor(config).run_until_clean(3)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["rounds"], 1)


if __name__ == "__main__":
    unittest.main()
