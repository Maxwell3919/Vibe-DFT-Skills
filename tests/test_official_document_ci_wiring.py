from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
ACTIVE_DISTRIBUTION = ROOT / "tools" / "build_active_only_distribution.py"


class OfficialDocumentCIWiringTests(unittest.TestCase):
    def test_workflow_keeps_full_history_and_fail_closed_baseline_selection(
        self,
    ) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertRegex(text, r"(?m)^\s+fetch-depth:\s+0\s*$")
        self.assertIn(
            "PR_BASE_SHA: ${{ github.event.pull_request.base.sha }}",
            text,
        )
        self.assertIn("PUSH_BEFORE_SHA: ${{ github.event.before }}", text)
        self.assertIn('task_baseline="$PR_BASE_SHA"', text)
        self.assertIn('task_baseline="$PUSH_BEFORE_SHA"', text)
        self.assertIn('task_baseline="HEAD^"', text)
        self.assertIn("git rev-parse --verify HEAD^", text)
        self.assertIn(
            "No trustworthy official-document migration baseline is available.",
            text,
        )
        self.assertRegex(
            text,
            r"No trustworthy official-document migration baseline "
            r"is available\.[\s\S]{0,80}\n\s+exit 2",
        )

    def test_one_validate_all_invocation_carries_baseline_and_tag_strict_mode(
        self,
    ) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertEqual(
            text.count("python tools/validate_all_skills.py"),
            1,
            "tag CI must not repeat the semantic bundle audit",
        )
        self.assertNotIn(
            "build_official_document_packs.py",
            text,
            "CI must inherit the canonical pack check from validate_all_skills.py",
        )
        self.assertIn('--baseline-ref "$task_baseline"', text)
        self.assertIn('if [[ "$GITHUB_REF" == refs/tags/* ]]', text)
        self.assertIn("task_release_args+=(--strict-release)", text)
        self.assertIn('"${task_release_args[@]}"', text)

    def test_active_only_portable_closure_includes_shared_content_policy(
        self,
    ) -> None:
        text = ACTIVE_DISTRIBUTION.read_text(encoding="utf-8")

        self.assertIn("import release_content_policy", text)
        self.assertIn('"tools/release_content_policy.py"', text)
        self.assertIn("release_content_policy.classify_path(", text)
        self.assertIn("release_content_policy.scan_path(", text)
        self.assertIn("release_content_policy.scan_bytes(", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
