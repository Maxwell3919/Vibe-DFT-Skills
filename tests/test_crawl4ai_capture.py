from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import crawl4ai_capture  # noqa: E402


def plan_args(**overrides):
    values = {
        "source_class": "official-package",
        "profile_id": "ase",
        "url": "https://ase-lib.org/ase/index.html",
        "fallback_condition": "browser-render-required",
        "native_evidence": "Synthetic native fetch omitted a browser-rendered navigation block.",
        "page_timeout_ms": 45000,
        "require_css": ["body"],
        "require_text": ["ASE"],
        "forbid_text": ["Access denied"],
        "minimum_markdown_bytes": 5,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def write_success_capture(artifact_root: Path):
    request = crawl4ai_capture.plan_request(plan_args(), ROOT)
    request_raw = crawl4ai_capture.canonical_json(request)
    (artifact_root / "request.json").write_bytes(request_raw)
    (artifact_root / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (artifact_root / "rendered.html").write_text(
        "<html><body>ASE</body></html>\n",
        encoding="utf-8",
    )
    (artifact_root / "content.md").write_text("# ASE\n", encoding="utf-8")
    captured = "2026-08-01T00:00:00Z"
    manifest = crawl4ai_capture.base_manifest(
        request,
        request_raw,
        captured,
        crawl4ai_capture.sha256(
            crawl4ai_capture.canonical_json(crawl4ai_capture.adapter_config(request))
        ),
    )
    manifest["status"] = "success"
    manifest["adapter"]["playwright_version"] = "1.55.0"
    manifest["adapter"]["browser_version"] = "Chromium 140.0.0.0"
    manifest["source"]["final_url"] = request["url"]
    robots_raw = (artifact_root / "robots.txt").read_bytes()
    manifest["policy"].update(
        {
            "robots_url": "https://ase-lib.org/robots.txt",
            "robots_status": "allowed",
            "robots_sha256": crawl4ai_capture.sha256(robots_raw),
            "robots_bytes": len(robots_raw),
            "minimum_delay_seconds": 1,
            "final_url_profile_verified": True,
        }
    )
    manifest["result"] = {
        "http_status": 200,
        "error_code": None,
        "content_gate_passed": True,
    }
    manifest["artifacts"] = [
        crawl4ai_capture.artifact(
            artifact_root / "request.json",
            "capture-request",
            "application/json",
            "request-evidence",
        ),
        crawl4ai_capture.artifact(
            artifact_root / "robots.txt",
            "robots-policy",
            "text/plain",
            "transport-evidence",
        ),
        crawl4ai_capture.artifact(
            artifact_root / "rendered.html",
            "rendered-dom",
            "text/html",
            "rendered-derivative",
        ),
        crawl4ai_capture.artifact(
            artifact_root / "content.md",
            "readable-markdown",
            "text/markdown",
            "readable-derivative",
        ),
    ]
    manifest_path = artifact_root / "manifest.json"
    manifest_path.write_bytes(crawl4ai_capture.canonical_json(manifest))
    return request, manifest, manifest_path


class Crawl4AICaptureTests(unittest.TestCase):
    def test_plan_is_closed_and_native_route_first(self) -> None:
        request = crawl4ai_capture.plan_request(plan_args(), ROOT)
        self.assertEqual(request["contract_name"], "web-source-capture-request")
        self.assertEqual(request["limits"]["max_pages"], 1)
        self.assertEqual(request["limits"]["max_depth"], 0)
        self.assertFalse(request["controls"]["allow_proxy"])
        self.assertFalse(request["controls"]["allow_llm_extraction"])
        self.assertEqual(
            crawl4ai_capture.schema_errors(
                request,
                crawl4ai_capture.load_schema(ROOT, crawl4ai_capture.REQUEST_SCHEMA),
            ),
            [],
        )

    def test_unregistered_or_disallowed_source_is_blocked(self) -> None:
        cases = (
            plan_args(profile_id="missing"),
            plan_args(url="https://user@ase-lib.org/ase/index.html"),
            plan_args(
                source_class="public-community",
                profile_id="keinsci-public",
                url="http://bbs.keinsci.com/search.php?mod=forum",
            ),
            plan_args(
                source_class="public-community",
                profile_id="keinsci-public",
                url="http://bbs.keinsci.com/forum.php?mod=viewthread&mod=post",
            ),
        )
        for item in cases:
            with self.subTest(item=item):
                with self.assertRaises(crawl4ai_capture.CaptureBlocked):
                    crawl4ai_capture.plan_request(item, ROOT)

    def test_active_official_authority_can_plan_but_planned_software_cannot(self) -> None:
        request = crawl4ai_capture.plan_request(
            plan_args(
                source_class="official-software",
                profile_id="qe-official-docs",
                url="https://www.quantum-espresso.org/Doc/INPUT_PW.html",
                require_css=["body"],
                require_text=["pw.x"],
            ),
            ROOT,
        )
        self.assertEqual(request["profile_id"], "qe-official-docs")
        with self.assertRaisesRegex(
            crawl4ai_capture.CaptureBlocked,
            "UNREGISTERED_OR_INACTIVE_OFFICIAL_AUTHORITY",
        ):
            crawl4ai_capture.plan_request(
                plan_args(
                    source_class="official-software",
                    profile_id="gaussian-official-reference",
                    url="https://gaussian.com/",
                ),
                ROOT,
            )

    def test_runtime_version_is_exact_and_missing_is_blocked(self) -> None:
        with mock.patch.object(
            crawl4ai_capture.importlib.metadata,
            "version",
            side_effect=crawl4ai_capture.importlib.metadata.PackageNotFoundError,
        ):
            with self.assertRaisesRegex(crawl4ai_capture.CaptureBlocked, "CRAWL4AI_RUNTIME_MISSING"):
                crawl4ai_capture.runtime_version()
        with mock.patch.object(crawl4ai_capture.importlib.metadata, "version", return_value="0.9.3"):
            with self.assertRaisesRegex(crawl4ai_capture.CaptureBlocked, "CRAWL4AI_VERSION_MISMATCH"):
                crawl4ai_capture.runtime_version()

    def test_output_inside_repository_and_existing_output_are_blocked(self) -> None:
        with self.assertRaisesRegex(crawl4ai_capture.CaptureBlocked, "OUTPUT_INSIDE_GIT_WORKTREE"):
            crawl4ai_capture.ensure_output_scope(ROOT / "capture", ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary)
            with self.assertRaisesRegex(crawl4ai_capture.CaptureBlocked, "OUTPUT_ALREADY_EXISTS"):
                crawl4ai_capture.ensure_output_scope(existing, ROOT)

    def test_success_manifest_hashes_and_claim_ceiling_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact_root = Path(temporary)
            _request, _manifest, manifest_path = write_success_capture(artifact_root)
            self.assertEqual(
                crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT),
                [],
            )
            (artifact_root / "content.md").write_text("tampered\n", encoding="utf-8")
            self.assertTrue(
                any(
                    "content identity mismatch" in item
                    for item in crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
                )
            )

    def test_success_manifest_semantics_are_cross_bound(self) -> None:
        cases = (
            ("adapter", "config_sha256", "0" * 64, "adapter configuration mismatch"),
            ("source", "final_url", "https://example.com/", "outside the bound profile"),
            ("result", "http_status", 404, "requires HTTP 2xx"),
            ("policy", "robots_sha256", "0" * 64, "robots receipt identity mismatch"),
            ("policy", "robots_url", "https://ase-lib.org/not-robots.txt", "does not match"),
            ("policy", "minimum_delay_seconds", 2, "delay receipt mismatch"),
        )
        for section, field, value, expected in cases:
            with self.subTest(section=section, field=field):
                with tempfile.TemporaryDirectory() as temporary:
                    artifact_root = Path(temporary)
                    _request, manifest, manifest_path = write_success_capture(artifact_root)
                    manifest[section][field] = value
                    manifest_path.write_bytes(crawl4ai_capture.canonical_json(manifest))
                    failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
                    self.assertTrue(any(expected in item for item in failures), failures)

    def test_validator_rejects_in_repository_or_unmanifested_capture_bytes(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            artifact_root = Path(temporary)
            _request, _manifest, manifest_path = write_success_capture(artifact_root)
            failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
            self.assertTrue(any("inside the Git worktree" in item for item in failures), failures)
        with tempfile.TemporaryDirectory() as temporary:
            artifact_root = Path(temporary)
            _request, _manifest, manifest_path = write_success_capture(artifact_root)
            (artifact_root / "unmanifested.txt").write_text("unexpected\n", encoding="utf-8")
            failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
            self.assertTrue(any("unmanifested" in item for item in failures), failures)

    def test_validator_rejects_forged_deterministic_ids_and_role_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact_root = Path(temporary)
            request, manifest, manifest_path = write_success_capture(artifact_root)
            request["request_id"] = f"capture-request-{'f' * 24}"
            request_raw = crawl4ai_capture.canonical_json(request)
            (artifact_root / "request.json").write_bytes(request_raw)
            manifest["request_ref"] = {
                "request_id": request["request_id"],
                "sha256": crawl4ai_capture.sha256(request_raw),
            }
            manifest["record_id"] = crawl4ai_capture.deterministic_record_id(
                request_raw,
                manifest["captured_utc"],
            )
            manifest["artifacts"][0] = crawl4ai_capture.artifact(
                artifact_root / "request.json",
                "capture-request",
                "application/json",
                "request-evidence",
            )
            manifest_path.write_bytes(crawl4ai_capture.canonical_json(manifest))
            failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
            self.assertTrue(any("deterministic identity mismatch" in item for item in failures), failures)
        with tempfile.TemporaryDirectory() as temporary:
            artifact_root = Path(temporary)
            _request, manifest, manifest_path = write_success_capture(artifact_root)
            manifest["record_id"] = f"web-capture-{'f' * 24}"
            manifest["artifacts"][0]["identity_role"] = "transport-evidence"
            manifest_path.write_bytes(crawl4ai_capture.canonical_json(manifest))
            failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
            self.assertTrue(any("record_id" in item for item in failures), failures)
            self.assertTrue(any("role identity mismatch" in item for item in failures), failures)

    def test_validator_returns_schema_failures_for_malformed_manifest_shapes(self) -> None:
        cases = (
            ("artifacts", None),
            ("source", "forged"),
            ("request_ref", "forged"),
            ("result", "forged"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary:
                    artifact_root = Path(temporary)
                    _request, manifest, manifest_path = write_success_capture(artifact_root)
                    manifest[field] = value
                    manifest_path.write_bytes(crawl4ai_capture.canonical_json(manifest))
                    failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
                    self.assertTrue(failures)

    def test_validator_returns_schema_failures_for_malformed_request_shapes(self) -> None:
        cases = (
            ("native_route", "forged"),
            ("content_gate", None),
            ("limits", []),
            ("controls", "forged"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary:
                    artifact_root = Path(temporary)
                    request, manifest, manifest_path = write_success_capture(artifact_root)
                    request[field] = value
                    request_raw = crawl4ai_capture.canonical_json(request)
                    (artifact_root / "request.json").write_bytes(request_raw)
                    manifest["request_ref"]["sha256"] = crawl4ai_capture.sha256(request_raw)
                    manifest["record_id"] = crawl4ai_capture.deterministic_record_id(
                        request_raw,
                        manifest["captured_utc"],
                    )
                    manifest["artifacts"][0] = crawl4ai_capture.artifact(
                        artifact_root / "request.json",
                        "capture-request",
                        "application/json",
                        "request-evidence",
                    )
                    manifest_path.write_bytes(crawl4ai_capture.canonical_json(manifest))
                    failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
                    self.assertTrue(any(item.startswith("request/") for item in failures), failures)

    def test_validator_replays_content_gate_from_hash_verified_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact_root = Path(temporary)
            _request, _manifest, manifest_path = write_success_capture(artifact_root)
            with mock.patch.object(
                Path,
                "read_text",
                side_effect=AssertionError("content artifacts must not be read twice"),
            ):
                failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
            self.assertEqual(failures, [])

    def test_request_semantics_use_the_single_verified_byte_snapshot(self) -> None:
        original_load_object = crawl4ai_capture.load_object

        def reject_second_request_read(path, *args, **kwargs):
            if Path(path).name in {"request.json", "source-request.json"}:
                raise AssertionError("request.json must not be read twice")
            return original_load_object(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            request = crawl4ai_capture.plan_request(plan_args(), ROOT)
            request_path = temporary_root / "source-request.json"
            request_path.write_bytes(crawl4ai_capture.canonical_json(request))
            output = temporary_root / "capture"
            with (
                mock.patch.object(
                    crawl4ai_capture,
                    "load_object",
                    side_effect=reject_second_request_read,
                ),
                mock.patch.object(
                    crawl4ai_capture,
                    "robots_receipt",
                    return_value=(
                        "https://ase-lib.org/robots.txt",
                        "blocked",
                        b"User-agent: *\nDisallow: /\n",
                        1,
                    ),
                ),
            ):
                exit_code, _manifest = crawl4ai_capture.run_capture(
                    request_path,
                    output,
                    ROOT,
                )
            self.assertEqual(exit_code, 3)
        with tempfile.TemporaryDirectory() as temporary:
            artifact_root = Path(temporary)
            _request, _manifest, manifest_path = write_success_capture(artifact_root)
            with mock.patch.object(
                crawl4ai_capture,
                "load_object",
                side_effect=reject_second_request_read,
            ):
                failures = crawl4ai_capture.validate_capture(manifest_path, artifact_root, ROOT)
            self.assertEqual(failures, [])

    def test_manifest_cannot_promote_browser_output_to_version_sensitive_use(self) -> None:
        request = crawl4ai_capture.plan_request(plan_args(), ROOT)
        manifest = crawl4ai_capture.base_manifest(
            request,
            crawl4ai_capture.canonical_json(request),
            "2026-08-01T00:00:00Z",
            "0" * 64,
        )
        promoted = copy.deepcopy(manifest)
        promoted["claim_ceiling"]["version_sensitive_use"] = True
        failures = crawl4ai_capture.schema_errors(
            promoted,
            crawl4ai_capture.load_schema(ROOT, crawl4ai_capture.MANIFEST_SCHEMA),
        )
        self.assertTrue(any("False was expected" in item for item in failures))

    def test_error_page_cannot_pass_a_target_content_gate(self) -> None:
        request = crawl4ai_capture.plan_request(
            plan_args(
                require_css=["#threadlist"],
                require_text=["第一性原理"],
                forbid_text=["提示信息"],
            ),
            ROOT,
        )
        self.assertFalse(
            crawl4ai_capture.content_gate_passes(
                request,
                "<html><body><h1>提示信息</h1></body></html>",
                "# 提示信息\n第一性原理\n",
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
