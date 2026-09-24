from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from genesis_bridge.config import BridgeConfig
from genesis_bridge.mcp_server import McpServer


class McpTests(unittest.TestCase):
    def test_initialize_and_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = BridgeConfig.load(Path(directory) / "config.json")
            config.data_dir = Path(directory) / "data"
            server = McpServer(config)
            initialized = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
            self.assertEqual(initialized["result"]["serverInfo"]["name"], "genesis-ai-bridge")
            tools = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            names = {item["name"] for item in tools["result"]["tools"]}
            self.assertIn("run_shared_file", names)

    def test_content_tool_uses_declared_ollama_provider_only(self) -> None:
        # This test validates policy before the network call: a content call is accepted
        # and the selected provider is explicit. Network behavior is covered by provider tests.
        with tempfile.TemporaryDirectory() as directory:
            config = BridgeConfig.load(Path(directory) / "config.json")
            config.data_dir = Path(directory) / "data"
            config.ollama_base_url = "http://127.0.0.1:9"
            server = McpServer(config)
            result = server.call("run_shared_file", {"filename": "x.txt", "content": "test", "task": "prüfen", "providers": ["ollama"]})
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["results"][0]["status"], "failed")

    def test_sensitive_or_outside_path_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            safe = root / "safe.txt"
            secret = root / ".env"
            safe.write_text("ok", encoding="utf-8")
            secret.write_text("TOKEN=not-used", encoding="utf-8")
            config = BridgeConfig.load(root / "config.json")
            config.data_dir = root / "data"
            config.mcp_allowed_roots = (root,)
            server = McpServer(config)
            with self.assertRaises(ValueError):
                server.call("run_shared_file", {"filename": ".env", "path": str(secret), "task": "prüfen", "providers": ["ollama"]})


if __name__ == "__main__":
    unittest.main()
