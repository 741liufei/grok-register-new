import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.registration.store import RegistrationRepository


OLD_SCHEMA = """
CREATE TABLE registration_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key TEXT UNIQUE,
    batch_id TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'gui',
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    duration_seconds REAL NOT NULL DEFAULT 0,
    email TEXT NOT NULL DEFAULT '',
    password TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'failure',
    success INTEGER NOT NULL DEFAULT 0,
    provider TEXT NOT NULL DEFAULT '',
    worker_id INTEGER NOT NULL DEFAULT 0,
    cpa_enabled INTEGER NOT NULL DEFAULT 0,
    cpa_status TEXT NOT NULL DEFAULT 'disabled',
    auth_info TEXT NOT NULL DEFAULT '',
    auth_path TEXT NOT NULL DEFAULT '',
    failure_type TEXT NOT NULL DEFAULT '',
    failure_reason TEXT NOT NULL DEFAULT '',
    account_file TEXT NOT NULL DEFAULT '',
    sso_saved INTEGER NOT NULL DEFAULT 0,
    nsfw_status TEXT NOT NULL DEFAULT '',
    extra_json TEXT NOT NULL DEFAULT '{}'
);
PRAGMA user_version = 1;
"""


class RegistrationRepositoryMigrationTests(unittest.TestCase):
    def test_old_database_migrates_and_filters_disable_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.sqlite3"
            with sqlite3.connect(path) as conn:
                conn.executescript(OLD_SCHEMA)
                conn.execute(
                    """
                    INSERT INTO registration_results
                    (started_at, finished_at, email, status, success, provider)
                    VALUES ('2026-08-01 00:00:00', '2026-08-01 00:00:01',
                            'old@example.com', 'success', 1, 'cloudflare')
                    """
                )

            store = RegistrationRepository(path)
            with sqlite3.connect(path) as conn:
                columns = {row[1] for row in conn.execute("PRAGMA table_info(registration_results)")}
                version = conn.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, 4)
            self.assertTrue(
                {
                    "email_account_id",
                    "email_disable_status",
                    "email_disabled_at",
                    "email_disable_error",
                    "cpa_auth_path",
                    "grok2api_auth_path",
                    "screenshot_path",
                    "cpa_remote_status",
                    "cpa_remote_imported_at",
                    "cpa_remote_error",
                    "grok2api_remote_status",
                    "grok2api_remote_imported_at",
                    "grok2api_remote_error",
                }.issubset(columns)
            )
            self.assertEqual(store.list_results()[0]["email_disable_status"], "not_applicable")

            store.add_result(
                {
                    "email": "disabled@outlook.com",
                    "status": "success",
                    "provider": "outlookemail",
                    "cpa_enabled": True,
                    "cpa_status": "success",
                    "email_account_id": "367",
                    "email_disable_status": "success",
                    "email_disabled_at": "2026-08-01 01:02:03",
                    "screenshot_path": "/tmp/failure.png",
                }
            )
            store.add_result(
                {
                    "email": "failed@outlook.com",
                    "status": "success",
                    "provider": "outlookemail",
                    "cpa_enabled": True,
                    "cpa_status": "success",
                    "email_disable_status": "failed",
                    "email_disable_error": "fixture error",
                }
            )

            filtered = store.list_results(email_disable_status="failed")
            self.assertEqual([row["email"] for row in filtered], ["failed@outlook.com"])
            self.assertEqual(store.count_results(), 3)
            self.assertEqual(len(store.list_results(limit=1, offset=1)), 1)
            self.assertEqual(
                store.count_results(email_disable_status="failed"), 1
            )
            stats = store.stats()
            self.assertEqual(stats["email_disabled"], 1)
            self.assertEqual(stats["email_disable_failed"], 1)
            disabled = next(row for row in store.list_results() if row["email"] == "disabled@outlook.com")
            self.assertEqual(disabled["screenshot_path"], "/tmp/failure.png")
            self.assertEqual(disabled["grok2api_remote_status"], "not_configured")

            self.assertTrue(
                store.update_remote_import_status(
                    disabled["id"], "grok2api", status="success"
                )
            )
            refreshed = store.get_results_by_ids([disabled["id"]])[0]
            self.assertEqual(refreshed["grok2api_remote_status"], "success")
            self.assertTrue(refreshed["grok2api_remote_imported_at"])


if __name__ == "__main__":
    unittest.main()
