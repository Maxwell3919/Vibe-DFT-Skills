from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import audit_privacy


class RepositoryPrivacyTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> None:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr.decode(errors="replace"))

    def _repository(self, root: Path) -> None:
        self._git(root, "init")
        self._git(root, "config", "user.email", "test@example.invalid")
        self._git(root, "config", "user.name", "Test User")

    def test_safe_placeholders_do_not_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            (root / "example.json").write_text(
                '{"path": "/home/<user>/case", "api_key": "redacted"}\n',
                encoding="utf-8",
            )
            self._git(root, "add", ".")
            self.assertEqual(audit_privacy.scan_worktree(root), [])

    def test_private_path_and_token_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            (root / "runtime.json").write_text(
                '{"path": "/home/preston/private-case", '
                '"value": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"}\n',
                encoding="utf-8",
            )
            self._git(root, "add", ".")
            codes = {finding.code for finding in audit_privacy.scan_worktree(root)}
            self.assertIn("PRIVACY_ABSOLUTE_PRIVATE_PATH", codes)
            self.assertIn("PRIVACY_GITHUB_TOKEN", codes)

    def test_restricted_runtime_filename_triggers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            (root / "POTCAR").write_text("synthetic placeholder\n", encoding="utf-8")
            self._git(root, "add", ".")
            codes = {finding.code for finding in audit_privacy.scan_worktree(root)}
            self.assertIn("PRIVACY_RESTRICTED_PATH", codes)

    def test_history_scan_finds_deleted_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            secret = root / "secret.txt"
            secret.write_text(
                "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n",
                encoding="utf-8",
            )
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "add secret")
            secret.unlink()
            self._git(root, "add", "-u")
            self._git(root, "commit", "-m", "remove secret")
            findings = audit_privacy.scan_history(root)
            self.assertTrue(
                any(
                    finding.code == "PRIVACY_SECRET_HISTORY"
                    and finding.path == "secret.txt"
                    for finding in findings
                )
            )


if __name__ == "__main__":
    unittest.main()
