import json
import tempfile
import unittest
from pathlib import Path

from backend.app import _load_account_auth_json


class WebAuthJsonTests(unittest.TestCase):
    def test_loads_cpa_and_grok2api_json_from_configured_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cpa_dir = root / "cpa"
            g2a_dir = root / "g2a"
            cpa_dir.mkdir()
            g2a_dir.mkdir()
            cpa_path = cpa_dir / "xai-user@outlook.com.json"
            g2a_path = g2a_dir / "g2a-user@outlook.com.json"
            cpa_path.write_text(json.dumps({"type": "xai", "email": "user@outlook.com"}), encoding="utf-8")
            g2a_path.write_text(json.dumps({"accounts": [{"email": "user@outlook.com"}]}), encoding="utf-8")
            record = {
                "email": "user@outlook.com",
                "auth_info": (
                    "CPA 本地: /stale/root/xai-user@outlook.com.json\n"
                    "Grok2API: /stale/root/g2a-user@outlook.com.json"
                ),
            }
            config = {
                "cpa_auth_dir": str(cpa_dir),
                "grok2api_auth_dir": str(g2a_dir),
            }

            cpa = _load_account_auth_json(record, config, "cpa")
            g2a = _load_account_auth_json(record, config, "grok2api")
            self.assertEqual(Path(cpa["path"]), cpa_path)
            self.assertEqual(Path(g2a["path"]), g2a_path)
            self.assertEqual(json.loads(cpa["content"])["email"], "user@outlook.com")
            self.assertEqual(json.loads(g2a["content"])["accounts"][0]["email"], "user@outlook.com")

    def test_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            _load_account_auth_json({}, {}, "other")


if __name__ == "__main__":
    unittest.main()
