from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_official_source_drift as drift  # noqa: E402


def _observation(
    *,
    commit: str | None = None,
    etag: str | None = None,
    content_sha256: str | None = None,
    state: str = "retrieved",
) -> dict:
    return {
        "authority_id": "example-authority",
        "provider_id": "example",
        "registered_identity": {
            "commit": commit,
            "revid": None,
            "tag": None,
        },
        "registered_snapshot": None,
        "registered_version_scopes": [],
        "retrieval": {
            "byte_count": 10 if state == "retrieved" else None,
            "content_sha256": content_sha256,
            "error_code": None if state == "retrieved" else "network-unavailable",
            "etag": etag,
            "final_identity": {
                "commit": commit,
                "revid": None,
                "tag": None,
            },
            "final_url": "https://example.org/docs/",
            "state": state,
            "status_code": 200 if state == "retrieved" else None,
        },
        "url": "https://example.org/docs/",
    }


class OfficialSourceDriftTests(unittest.TestCase):
    def test_exact_identity_etag_and_hash_changes_are_the_only_drift_fields(self) -> None:
        baseline = _observation(
            commit="a" * 40,
            etag='"old"',
            content_sha256="b" * 64,
        )
        current = _observation(
            commit="c" * 40,
            etag='"new"',
            content_sha256="d" * 64,
        )
        comparison = drift.compare_observation(current, baseline)
        self.assertEqual(comparison["state"], "drifted")
        self.assertEqual(
            comparison["drift_fields"],
            ["commit", "etag", "content_sha256"],
        )
        self.assertNotIn("status_code", comparison["drift_fields"])

    def test_network_unavailable_is_not_mislabeled_as_drift(self) -> None:
        baseline = _observation(
            commit="a" * 40,
            etag='"old"',
            content_sha256="b" * 64,
        )
        current = _observation(commit="a" * 40, state="unavailable")
        comparison = drift.compare_observation(current, baseline)
        self.assertEqual(comparison["state"], "unavailable")
        self.assertEqual(comparison["drift_fields"], [])

    def test_redirected_commit_identity_drift_is_detected_without_a_baseline(self) -> None:
        current = _observation(commit="a" * 40)
        current["retrieval"]["final_identity"]["commit"] = "b" * 40
        comparison = drift.compare_observation(current, None)
        self.assertEqual(comparison["state"], "drifted")
        self.assertEqual(comparison["drift_fields"], ["commit"])

    def test_report_generation_is_deterministic_and_conservative(self) -> None:
        authorities = {
            "example-authority": {
                "provider_id": "example",
                "canonical_urls": [
                    "https://example.org/project/raw/" + "a" * 40 + "/"
                ],
                "version_scopes": [
                    {
                        "scope": "exact",
                        "exact_version": "1.2.3",
                        "minimum_version": None,
                        "maximum_version": None,
                        "release_series": None,
                    }
                ],
                "canonical_snapshot": None,
            }
        }

        def fetcher(url: str, allowed_origins: tuple[str, ...]) -> dict:
            del allowed_origins
            return {
                "byte_count": 4,
                "content_sha256": "e" * 64,
                "error_code": None,
                "etag": '"fixture"',
                "final_url": url,
                "state": "retrieved",
                "status_code": 200,
            }

        first = drift.build_report_from_authorities(
            authorities,
            registry_sha256="f" * 64,
            observed_utc="2026-07-24T00:00:00Z",
            fetcher=fetcher,
        )
        second = drift.build_report_from_authorities(
            authorities,
            registry_sha256="f" * 64,
            observed_utc="2026-07-24T00:00:00Z",
            fetcher=fetcher,
        )
        self.assertEqual(drift.report_bytes(first), drift.report_bytes(second))
        self.assertEqual(first["summary"]["unbaselined"], 1)
        self.assertEqual(first["summary"]["drifted"], 0)
        self.assertEqual(
            first["comparison_policy"]["drift_fields"],
            ["tag", "commit", "revid", "etag", "content_sha256"],
        )

    def test_output_guard_rejects_registry_and_pack_mutation_targets(self) -> None:
        bad_paths = (
            ROOT / "registry" / "drift.json",
            ROOT
            / "skills"
            / "qe-rigorous-calculations"
            / "references"
            / "official-source-pack"
            / "drift.json",
        )
        for path in bad_paths:
            with self.subTest(path=path), self.assertRaises(drift.DriftError):
                drift.validate_output_path(ROOT, path)
        with tempfile.TemporaryDirectory() as temporary:
            allowed = Path(temporary) / "drift.json"
            self.assertEqual(drift.validate_output_path(ROOT, allowed), allowed.resolve())

    def test_scheduled_workflow_is_live_only_and_never_pushes(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "official-source-drift.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("schedule:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("check_official_source_drift.py", workflow)
        self.assertNotIn("git commit", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("--fail-on-drift", workflow)


if __name__ == "__main__":
    unittest.main()
