from __future__ import annotations

import unittest

from genesis_bridge.openclaw import extract_text


class OpenClawAdapterTests(unittest.TestCase):
    def test_extracts_common_json_shapes(self) -> None:
        self.assertEqual(extract_text('{"reply":"Hallo"}'), "Hallo")
        self.assertEqual(extract_text('{"result":{"content":"Welt"}}'), "Welt")
        self.assertEqual(extract_text('plain output'), "plain output")


if __name__ == "__main__":
    unittest.main()
