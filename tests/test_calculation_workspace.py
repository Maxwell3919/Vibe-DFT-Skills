from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "manage_calculation_workspace.py"


class CalculationWorkspaceTests(unittest.TestCase):
    def run_tool(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def test_silent_workspace_has_ordered_layout_and_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.run_tool(
                "init",
                str(workspace),
                "--case-id",
                "case-anon-001",
                "--protocol-id",
                "protocol-pbe-001",
                "--objective",
                "Converge a named observable",
                "--review-mode",
                "silent-update",
                "--selected-utc",
                "2026-07-26T10:00:00Z",
            )
            artifact = workspace / "01-structures" / "input.cif"
            artifact.write_text("data_synthetic\n", encoding="utf-8")
            update = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "structure-ready",
                "--stage-title",
                "Initial structure",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Recorded stable structure bytes",
                "--artifact",
                "structure=01-structures/input.cif",
                "--at-utc",
                "2026-07-26T11:00:00Z",
            )
            self.assertFalse(json.loads(update.stdout)["pause_required"])
            check = json.loads(self.run_tool("check", str(workspace)).stdout)
            self.assertEqual(check["revision"], 2)
            first = (
                workspace
                / "00-governance"
                / "taskbook-revisions"
                / "revision-000001.json"
            ).read_bytes()
            second = json.loads(
                (
                    workspace
                    / "00-governance"
                    / "taskbook-revisions"
                    / "revision-000002.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                second["previous_revision"]["sha256"],
                hashlib.sha256(first).hexdigest(),
            )

    def test_milestone_review_pauses_and_requires_approval_for_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.run_tool(
                "init",
                str(workspace),
                "--case-id",
                "case-anon-002",
                "--protocol-id",
                "protocol-pbe-002",
                "--objective",
                "Review each milestone",
                "--review-mode",
                "milestone-review",
                "--selected-utc",
                "2026-07-26T10:00:00Z",
            )
            pending = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--stage-status",
                "pending-review",
                "--review-state",
                "pending-review",
                "--summary",
                "Inputs await user review",
                "--at-utc",
                "2026-07-26T11:00:00Z",
            )
            self.assertTrue(json.loads(pending.stdout)["pause_required"])
            self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--stage-status",
                "completed",
                "--review-state",
                "pending-review",
                "--summary",
                "Cannot complete without approval",
                "--at-utc",
                "2026-07-26T11:10:00Z",
                expected=2,
            )
            self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--stage-status",
                "completed",
                "--review-state",
                "approved",
                "--review-note",
                "User approved this recorded milestone",
                "--summary",
                "Recorded user approval",
                "--at-utc",
                "2026-07-26T11:20:00Z",
            )
            self.run_tool("check", str(workspace))

    def test_off_mode_creates_layout_without_taskbook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.run_tool(
                "init",
                str(workspace),
                "--case-id",
                "case-anon-003",
                "--protocol-id",
                "protocol-pbe-003",
                "--objective",
                "No taskbook requested",
                "--review-mode",
                "off",
                "--selected-utc",
                "2026-07-26T10:00:00Z",
            )
            result = json.loads(self.run_tool("check", str(workspace)).stdout)
            self.assertFalse(result["taskbook_enabled"])
            self.assertFalse(
                (workspace / "00-governance" / "taskbook-current.json").exists()
            )

    def test_artifact_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.run_tool(
                "init",
                str(workspace),
                "--case-id",
                "case-anon-004",
                "--protocol-id",
                "protocol-pbe-004",
                "--objective",
                "Detect evidence drift",
                "--review-mode",
                "silent-update",
                "--selected-utc",
                "2026-07-26T10:00:00Z",
            )
            artifact = workspace / "04-derived" / "table.csv"
            artifact.write_text("x,y\n1,2\n", encoding="utf-8")
            self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "data-ready",
                "--stage-title",
                "Derived data",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Recorded stable table",
                "--artifact",
                "dataset=04-derived/table.csv",
                "--at-utc",
                "2026-07-26T11:00:00Z",
            )
            relabeled = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "figure-ready",
                "--stage-title",
                "Figure",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Cannot relabel recorded bytes as another artifact kind",
                "--artifact",
                "figure=04-derived/table.csv",
                "--at-utc",
                "2026-07-26T11:30:00Z",
                expected=2,
            )
            self.assertIn("recorded artifact labels are immutable", relabeled.stderr)
            artifact.write_text("x,y\n1,3\n", encoding="utf-8")
            failed = self.run_tool("check", str(workspace), expected=2)
            self.assertIn("artifact hash drift", failed.stderr)
            rejected = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "data-ready",
                "--stage-title",
                "Derived data",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Cannot overwrite recorded artifact identity",
                "--artifact",
                "dataset=04-derived/table.csv",
                "--at-utc",
                "2026-07-26T12:00:00Z",
                expected=2,
            )
            self.assertTrue(
                "artifact hash drift" in rejected.stderr
                or "recorded artifact labels are immutable" in rejected.stderr
            )


if __name__ == "__main__":
    unittest.main()
