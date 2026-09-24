from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from genesis_bridge.config import BridgeConfig
from genesis_bridge.installer import install_claude_mcp


class InstallerTests(unittest.TestCase):
    def test_claude_config_merge_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = BridgeConfig.load(root / "bridge.json")
            config.data_dir = root / "data"
            target = root / "claude_desktop_config.json"
            target.write_text(json.dumps({"mcpServers": {"existing": {"command": "x"}}}), encoding="utf-8")
            result = install_claude_mcp(config, target)
            document = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn("existing", document["mcpServers"])
            self.assertIn("genesis-ai-bridge", document["mcpServers"])
            self.assertIsNotNone(result["backup"])
            self.assertTrue(Path(result["backup"]).exists())

    def test_invalid_config_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = BridgeConfig.load(root / "bridge.json")
            target = root / "claude_desktop_config.json"
            target.write_text("{ kaputt", encoding="utf-8")
            with self.assertRaises(ValueError):
                install_claude_mcp(config, target)
            self.assertEqual(target.read_text(encoding="utf-8"), "{ kaputt")


if __name__ == "__main__":
    unittest.main()
