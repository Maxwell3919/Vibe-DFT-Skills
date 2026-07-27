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
    def run_tool(
        self, *arguments: str, expected: int = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def init_workspace(
        self, workspace: Path, mode: str = "silent-update", case: str = "case-anon-001"
    ) -> dict[str, object]:
        result = self.run_tool(
            "init",
            str(workspace),
            "--case-id",
            case,
            "--protocol-id",
            "protocol-pbe-001",
            "--objective",
            "Converge a named observable",
            "--review-mode",
            mode,
            "--selected-utc",
            "2026-07-26T10:00:00Z",
        )
        return json.loads(result.stdout)

    def create_input_set(
        self,
        workspace: Path,
        *,
        stage_id: str = "static-stage",
        input_set_id: str = "inputs-v001",
        engine_id: str = "qe",
    ) -> str:
        input_root = workspace / "02-inputs" / stage_id / input_set_id
        input_root.mkdir(parents=True, exist_ok=True)
        input_file = input_root / "calculation.in"
        input_file.write_text("&CONTROL\n calculation='scf'\n/\n", encoding="utf-8")
        relative_input = input_file.relative_to(workspace).as_posix()
        result = self.run_tool(
            "create-input-set",
            str(workspace),
            "--stage-id",
            stage_id,
            "--input-set-id",
            input_set_id,
            "--engine-id",
            engine_id,
            "--input",
            f"main-input={relative_input}",
            "--at-utc",
            "2026-07-26T10:10:00Z",
        )
        return str(json.loads(result.stdout)["input_set"])

    def approve_initial_review(
        self, workspace: Path, input_set: str
    ) -> dict[str, object]:
        plan = workspace / "00-governance" / "plans" / "workflow-plan.json"
        plan.write_text('{"format_name":"workflow-plan","version":"synthetic"}\n')
        request = json.loads(
            self.run_tool(
                "request-initial-review",
                str(workspace),
                "--workflow-plan",
                plan.relative_to(workspace).as_posix(),
                "--input-set",
                input_set,
                "--summary",
                "Freeze the reviewed workflow plan and exact input set",
                "--at-utc",
                "2026-07-26T10:20:00Z",
            ).stdout
        )
        return json.loads(
            self.run_tool(
                "decide-initial-review",
                str(workspace),
                "--decision",
                "approved",
                "--expected-taskbook-sha256",
                str(request["taskbook_sha256"]),
                "--review-note",
                "User reviewed the frozen plan and input set",
                "--at-utc",
                "2026-07-26T10:30:00Z",
            ).stdout
        )

    def test_silent_workspace_has_ordered_layout_and_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            initialized = self.init_workspace(workspace)
            self.assertEqual(initialized["initial_review_state"], "not-required")
            artifact = workspace / "01-structures" / "input.cif"
            artifact.write_text("data_synthetic\n", encoding="utf-8")
            update = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "structure-ready",
                "--stage-title",
                "Initial structure",
                "--milestone-kind",
                "structure",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Recorded stable structure bytes",
                "--next-action",
                "Prepare the calculation input set",
                "--artifact",
                "structure=01-structures/input.cif",
                "--at-utc",
                "2026-07-26T11:00:00Z",
            )
            self.assertFalse(json.loads(update.stdout)["pause_required"])
            check = json.loads(self.run_tool("check", str(workspace)).stdout)
            self.assertEqual(check["revision"], 2)
            self.assertTrue(check["execution_review_ready"])
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
            self.assertEqual(
                second["stages"][0]["next_action"],
                "Prepare the calculation input set",
            )

    def test_initial_review_binds_exact_plan_and_input_before_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            initialized = self.init_workspace(
                workspace, mode="milestone-review", case="case-anon-002"
            )
            self.assertEqual(
                initialized["initial_review_state"], "awaiting-request"
            )
            input_set = self.create_input_set(workspace)
            blocked = self.run_tool(
                "init-attempt",
                str(workspace),
                "--stage-id",
                "static-stage",
                "--attempt-id",
                "attempt-001",
                "--engine-id",
                "qe",
                "--input-set",
                input_set,
                "--summary",
                "Prepare the first attempt",
                "--at-utc",
                "2026-07-26T10:15:00Z",
                expected=2,
            )
            self.assertIn("before initial review approval", blocked.stderr)
            plan = workspace / "00-governance" / "plans" / "workflow-plan.json"
            plan.write_text('{"route":"synthetic"}\n', encoding="utf-8")
            request = json.loads(
                self.run_tool(
                    "request-initial-review",
                    str(workspace),
                    "--workflow-plan",
                    plan.relative_to(workspace).as_posix(),
                    "--input-set",
                    input_set,
                    "--summary",
                    "Present exact plan and input bytes",
                    "--at-utc",
                    "2026-07-26T10:20:00Z",
                ).stdout
            )
            self.assertTrue(request["pause_required"])
            stale = self.run_tool(
                "decide-initial-review",
                str(workspace),
                "--decision",
                "approved",
                "--expected-taskbook-sha256",
                "0" * 64,
                "--review-note",
                "Stale review must not apply",
                "--at-utc",
                "2026-07-26T10:25:00Z",
                expected=2,
            )
            self.assertIn("stale initial review decision", stale.stderr)
            approved = json.loads(
                self.run_tool(
                    "decide-initial-review",
                    str(workspace),
                    "--decision",
                    "approved",
                    "--expected-taskbook-sha256",
                    request["taskbook_sha256"],
                    "--review-note",
                    "User reviewed the frozen plan and input set",
                    "--at-utc",
                    "2026-07-26T10:30:00Z",
                ).stdout
            )
            self.assertTrue(approved["execution_review_ready"])
            prepared = json.loads(
                self.run_tool(
                    "init-attempt",
                    str(workspace),
                    "--stage-id",
                    "static-stage",
                    "--attempt-id",
                    "attempt-001",
                    "--engine-id",
                    "qe",
                    "--input-set",
                    input_set,
                    "--summary",
                    "Materialize the approved attempt",
                    "--at-utc",
                    "2026-07-26T10:40:00Z",
                ).stdout
            )
            self.assertEqual(prepared["initial_review_state"], "approved")
            self.assertTrue(
                (
                    workspace
                    / "03-runs/static-stage/attempt-001/calculation.in"
                ).is_file()
            )
            self.run_tool("check", str(workspace))

    def test_attempt_lifecycle_blocks_reorganization_while_active(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.init_workspace(workspace, case="case-anon-003")
            input_set = self.create_input_set(workspace)
            self.run_tool(
                "init-attempt",
                str(workspace),
                "--stage-id",
                "static-stage",
                "--attempt-id",
                "attempt-001",
                "--engine-id",
                "qe",
                "--input-set",
                input_set,
                "--summary",
                "Prepared from the immutable input set",
                "--at-utc",
                "2026-07-26T10:20:00Z",
            )
            self.run_tool(
                "append-attempt-event",
                str(workspace),
                "--stage-id",
                "static-stage",
                "--attempt-id",
                "attempt-001",
                "--state",
                "active",
                "--summary",
                "External executor reported the attempt active",
                "--at-utc",
                "2026-07-26T10:30:00Z",
            )
            check = json.loads(self.run_tool("check", str(workspace)).stdout)
            self.assertEqual(check["active_attempts"], ["static-stage/attempt-001"])
            self.assertFalse(check["workspace_reorganization_allowed"])
            quiescent = self.run_tool(
                "check", str(workspace), "--require-quiescent", expected=2
            )
            self.assertIn("workspace is not quiescent", quiescent.stderr)
            attempt_root = workspace / "03-runs/static-stage/attempt-001"
            run_record = attempt_root / "run-manifest.json"
            run_record.write_text('{"status":"completed"}\n', encoding="utf-8")
            self.run_tool(
                "append-attempt-event",
                str(workspace),
                "--stage-id",
                "static-stage",
                "--attempt-id",
                "attempt-001",
                "--state",
                "completed",
                "--summary",
                "Recorded terminal application evidence",
                "--artifact",
                "run-record=03-runs/static-stage/attempt-001/run-manifest.json",
                "--at-utc",
                "2026-07-26T11:00:00Z",
            )
            final = json.loads(
                self.run_tool(
                    "check", str(workspace), "--require-quiescent"
                ).stdout
            )
            self.assertTrue(final["workspace_reorganization_allowed"])
            self.assertEqual(final["active_attempts"], [])

    def test_reviewed_milestone_requires_artifact_and_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.init_workspace(
                workspace, mode="milestone-review", case="case-anon-004"
            )
            input_set = self.create_input_set(workspace)
            self.approve_initial_review(workspace, input_set)
            pending = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--milestone-kind",
                "input",
                "--stage-status",
                "pending-review",
                "--review-state",
                "pending-review",
                "--summary",
                "Inputs await user review",
                "--next-action",
                "Wait for the input milestone decision",
                "--artifact",
                f"input-set={input_set}",
                "--at-utc",
                "2026-07-26T11:00:00Z",
            )
            self.assertTrue(json.loads(pending.stdout)["pause_required"])
            rejected = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--milestone-kind",
                "input",
                "--stage-status",
                "completed",
                "--review-state",
                "pending-review",
                "--summary",
                "Cannot complete without approval",
                "--next-action",
                "Wait",
                "--at-utc",
                "2026-07-26T11:10:00Z",
                expected=2,
            )
            self.assertIn("requires approved", rejected.stderr)
            self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--milestone-kind",
                "input",
                "--stage-status",
                "completed",
                "--review-state",
                "approved",
                "--review-note",
                "User approved this recorded milestone",
                "--summary",
                "Recorded user approval",
                "--next-action",
                "Start only under separate execution authority",
                "--at-utc",
                "2026-07-26T11:20:00Z",
            )
            regression = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "inputs-ready",
                "--stage-title",
                "Calculation inputs",
                "--milestone-kind",
                "input",
                "--stage-status",
                "running",
                "--review-state",
                "approved",
                "--review-note",
                "Invalid regression",
                "--summary",
                "Attempt to reopen a completed milestone",
                "--next-action",
                "Stop",
                "--at-utc",
                "2026-07-26T11:30:00Z",
                expected=2,
            )
            self.assertIn(
                "approved reviewed milestone must be completed",
                regression.stderr,
            )

    def test_structure_data_and_figure_milestones_require_typed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.init_workspace(workspace, case="case-anon-005")
            missing = self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "data-ready",
                "--stage-title",
                "Derived data",
                "--milestone-kind",
                "data",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "A data milestone cannot be evidence-free",
                "--next-action",
                "Write stable normalized data",
                "--at-utc",
                "2026-07-26T11:00:00Z",
                expected=2,
            )
            self.assertIn("requires a dataset artifact", missing.stderr)
            dataset = workspace / "04-derived" / "data-ready" / "table.csv"
            dataset.parent.mkdir(parents=True)
            dataset.write_text("x,y\n1,2\n", encoding="utf-8")
            self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "data-ready",
                "--stage-title",
                "Derived data",
                "--milestone-kind",
                "data",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Recorded normalized data",
                "--next-action",
                "Render a figure from this exact dataset",
                "--artifact",
                "dataset=04-derived/data-ready/table.csv",
                "--at-utc",
                "2026-07-26T11:10:00Z",
            )
            figure = workspace / "05-figures" / "figure-ready" / "plot.svg"
            figure.parent.mkdir(parents=True)
            figure.write_text("<svg></svg>\n", encoding="utf-8")
            self.run_tool(
                "update",
                str(workspace),
                "--stage-id",
                "figure-ready",
                "--stage-title",
                "Auditable figure",
                "--milestone-kind",
                "figure",
                "--stage-status",
                "completed",
                "--review-state",
                "not-required",
                "--summary",
                "Recorded the figure bytes",
                "--next-action",
                "Prepare the human-readable report",
                "--artifact",
                "figure=05-figures/figure-ready/plot.svg",
                "--at-utc",
                "2026-07-26T11:20:00Z",
            )
            current = json.loads(
                (
                    workspace / "00-governance/taskbook-current.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                {stage["milestone_kind"] for stage in current["stages"]},
                {"data", "figure"},
            )

    def test_off_mode_creates_layout_without_taskbook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.init_workspace(workspace, mode="off", case="case-anon-006")
            result = json.loads(self.run_tool("check", str(workspace)).stdout)
            self.assertFalse(result["taskbook_enabled"])
            self.assertTrue(result["execution_review_ready"])
            self.assertFalse(
                (workspace / "00-governance" / "taskbook-current.json").exists()
            )

    def test_artifact_and_materialized_input_drift_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.init_workspace(workspace, case="case-anon-007")
            input_set = self.create_input_set(workspace)
            self.run_tool(
                "init-attempt",
                str(workspace),
                "--stage-id",
                "static-stage",
                "--attempt-id",
                "attempt-001",
                "--engine-id",
                "qe",
                "--input-set",
                input_set,
                "--summary",
                "Prepare immutable input bytes",
                "--at-utc",
                "2026-07-26T10:20:00Z",
            )
            copied = workspace / "03-runs/static-stage/attempt-001/calculation.in"
            copied.write_text("&CONTROL\n calculation='relax'\n/\n", encoding="utf-8")
            failed = self.run_tool("check", str(workspace), expected=2)
            self.assertIn("materialized input bytes drifted", failed.stderr)

    def test_unmanaged_input_and_attempt_directories_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            self.init_workspace(workspace, case="case-anon-008")
            unmanaged_input = workspace / "02-inputs/static-stage/inputs-v001"
            unmanaged_input.mkdir(parents=True)
            failed_input = self.run_tool("check", str(workspace), expected=2)
            self.assertIn("unmanaged input-set directory", failed_input.stderr)
            unmanaged_input.rmdir()
            unmanaged_run = workspace / "03-runs/static-stage/attempt-001"
            unmanaged_run.mkdir(parents=True)
            failed_run = self.run_tool("check", str(workspace), expected=2)
            self.assertIn("unmanaged attempt directory", failed_run.stderr)


if __name__ == "__main__":
    unittest.main()
