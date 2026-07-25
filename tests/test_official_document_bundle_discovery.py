from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_official_document_bundles as bundle_audit  # noqa: E402


class OfficialDocumentBundleDiscoveryTests(unittest.TestCase):
    def make_repository(
        self,
        directory: str,
        *,
        registered_skills: tuple[str, ...] = ("source-skill",),
    ) -> Path:
        root = Path(directory)
        (root / "registry").mkdir(parents=True)
        rows = [
            "schema_version: '1.0'",
            "skills:",
        ]
        for skill_id in registered_skills:
            rows.extend(
                [
                    f"  {skill_id}:",
                    "    lifecycle: development",
                    f"    path: skills/{skill_id}",
                ]
            )
            (root / "skills" / skill_id / "references").mkdir(parents=True)
        rows.extend(
            [
                "  planned-skill:",
                "    lifecycle: planned",
                "    path: null",
            ]
        )
        (root / "registry" / "skill-registry.yaml").write_text(
            "\n".join(rows) + "\n",
            encoding="utf-8",
        )
        expectation_rows = [
            "schema_version: '1.0'",
            "migration_policy:",
            "  temporary: true",
            "  removal_condition: replace-with-pack-required-when-first-pack-is-added",
            "  downgrade_policy: forbidden",
            "skills:",
        ]
        for skill_id in registered_skills:
            expectation_rows.extend(
                [
                    f"  {skill_id}:",
                    "    expectation: legacy-missing",
                    (
                        "    entrypoint: "
                        f"skills/{skill_id}/references/official-source-pack/bundle.json"
                    ),
                ]
            )
        (root / "registry" / "official-document-bundle-expectations.yaml").write_text(
            "\n".join(expectation_rows) + "\n",
            encoding="utf-8",
        )
        tools = root / "tools"
        tools.mkdir()
        validator = tools / "validate_official_document_coverage.py"
        validator.write_text(
            "from pathlib import Path\n"
            "raise SystemExit(int(Path(__file__).with_name('validator-exit').read_text()))\n",
            encoding="utf-8",
        )
        tools.joinpath("validator-exit").write_text("0", encoding="utf-8")
        return root

    def make_bundle(
        self,
        root: Path,
        *,
        skill_id: str = "source-skill",
        index_overrides: dict[str, object] | None = None,
    ) -> Path:
        pack = root / "skills" / skill_id / "references" / "official-source-pack"
        pack.mkdir(parents=True, exist_ok=True)
        records = {
            "corpora": ["corpus.json"],
            "slice_manifests": ["slices.json"],
            "scope_inventory": "scope-inventory.json",
            "coverage": "coverage.json",
        }
        for filename in (
            "corpus.json",
            "slices.json",
        ):
            pack.joinpath(filename).write_text("{}\n", encoding="utf-8")
        for filename in ("scope-inventory.json", "coverage.json"):
            pack.joinpath(filename).write_text(
                json.dumps({"skill_id": skill_id}) + "\n",
                encoding="utf-8",
            )
        index: dict[str, object] = {
            "bundle_type": "official-document-coverage",
            "schema_version": "1.0",
            "skill_id": skill_id,
            "records": records,
        }
        if index_overrides:
            index.update(index_overrides)
        pack.joinpath("bundle.json").write_text(
            json.dumps(index, indent=2) + "\n",
            encoding="utf-8",
        )
        self.set_expectation(root, skill_id, "pack-required")
        return pack

    def set_expectation(self, root: Path, skill_id: str, expectation: str) -> None:
        registry = root / "registry" / "official-document-bundle-expectations.yaml"
        text = registry.read_text(encoding="utf-8")
        old = (
            f"  {skill_id}:\n"
            "    expectation: legacy-missing\n"
        )
        if old not in text:
            old = (
                f"  {skill_id}:\n"
                "    expectation: pack-required\n"
            )
        self.assertIn(old, text)
        registry.write_text(
            text.replace(
                old,
                f"  {skill_id}:\n    expectation: {expectation}\n",
                1,
            ),
            encoding="utf-8",
        )

    def test_missing_bundle_is_reported_and_only_blocks_strict_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.counts, {"complete": 0, "partial": 0, "missing": 1, "invalid": 0})
        self.assertEqual(report.results[0].skill_id, "source-skill")
        self.assertIn("bundle.json", report.results[0].message)
        self.assertEqual(bundle_audit.exit_code(report, strict_release=False), 0)
        self.assertEqual(bundle_audit.exit_code(report, strict_release=True), 3)

    def test_pack_without_registration_entry_is_invalid_not_legacy_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.set_expectation(root, "source-skill", "pack-required")
            pack = root / "skills" / "source-skill" / "references" / "official-source-pack"
            pack.mkdir()
            pack.joinpath("corpus.json").write_text("{}\n", encoding="utf-8")
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("registration", report.results[0].message)
        self.assertEqual(bundle_audit.exit_code(report, strict_release=False), 2)

    def test_expectation_registry_is_exact_and_pack_required_missing_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.set_expectation(root, "source-skill", "pack-required")
            required_missing = bundle_audit.audit_repository(root)
            self.assertEqual(required_missing.results[0].state, "invalid")
            self.assertIn("required", required_missing.results[0].message)
            self.assertEqual(
                bundle_audit.exit_code(required_missing, strict_release=False),
                2,
            )

            expectation_registry = (
                root / "registry" / "official-document-bundle-expectations.yaml"
            )
            expectation_registry.write_text(
                expectation_registry.read_text(encoding="utf-8").replace(
                    "  source-skill:\n",
                    "  unknown-skill:\n",
                ),
                encoding="utf-8",
            )
            mismatch = bundle_audit.audit_repository(root)

        self.assertEqual(mismatch.results[0].state, "invalid")
        self.assertIn("exactly match", mismatch.results[0].message)

    def test_legacy_missing_expectation_cannot_hide_an_added_pack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            self.set_expectation(root, "source-skill", "legacy-missing")
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("pack-required", report.results[0].message)

    def test_unknown_registry_lifecycle_is_invalid_not_silently_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            registry = root / "registry" / "skill-registry.yaml"
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    "lifecycle: planned",
                    "lifecycle: invented",
                ),
                encoding="utf-8",
            )
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("lifecycle", report.results[0].message)

    def test_unhashable_registry_values_return_invalid_instead_of_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            skill_registry = root / "registry" / "skill-registry.yaml"
            skill_registry.write_text(
                skill_registry.read_text(encoding="utf-8").replace(
                    "lifecycle: planned",
                    "lifecycle: [planned]",
                ),
                encoding="utf-8",
            )
            lifecycle_report = bundle_audit.audit_repository(root)
            self.assertEqual(lifecycle_report.results[0].state, "invalid")

            root = self.make_repository(str(Path(directory) / "second"))
            expectation_registry = (
                root / "registry" / "official-document-bundle-expectations.yaml"
            )
            expectation_registry.write_text(
                expectation_registry.read_text(encoding="utf-8").replace(
                    "expectation: legacy-missing",
                    "expectation: [legacy-missing]",
                ),
                encoding="utf-8",
            )
            expectation_report = bundle_audit.audit_repository(root)

        self.assertEqual(expectation_report.results[0].state, "invalid")

    def test_malformed_registration_and_missing_required_record_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            pack = self.make_bundle(root)
            pack.joinpath("bundle.json").write_text('{"schema_version":"1.0",', encoding="utf-8")
            malformed = bundle_audit.audit_repository(root)
            self.assertEqual(malformed.results[0].state, "invalid")

            self.make_bundle(root)
            pack.joinpath("coverage.json").unlink()
            missing = bundle_audit.audit_repository(root)
            self.assertEqual(missing.results[0].state, "invalid")
            self.assertIn("registered file is missing", missing.results[0].message)

    def test_unregistered_pack_file_and_unregistered_skill_pack_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            pack = self.make_bundle(root)
            pack.joinpath("orphan.json").write_text("{}\n", encoding="utf-8")
            orphan_file = bundle_audit.audit_repository(root)
            self.assertEqual(orphan_file.results[0].state, "invalid")
            self.assertIn("unregistered", orphan_file.results[0].message)

            pack.joinpath("orphan.json").unlink()
            unregistered = root / "skills" / "unregistered-skill" / "references" / "official-source-pack"
            unregistered.mkdir(parents=True)
            unregistered.joinpath("bundle.json").write_text("{}\n", encoding="utf-8")
            orphan_pack = bundle_audit.audit_repository(root)
            self.assertTrue(
                any(
                    result.skill_id == "unregistered-skill" and result.state == "invalid"
                    for result in orphan_pack.results
                )
            )

    def test_hardlinked_registration_is_rejected_before_json_bytes_are_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            pack = self.make_bundle(root)
            entrypoint = pack / "bundle.json"
            external = root / "external-registration.json"
            entrypoint.replace(external)
            os.link(external, entrypoint)
            with mock.patch.object(
                bundle_audit.strict_json,
                "load_object",
                side_effect=AssertionError("unsafe entrypoint was read"),
            ) as loader:
                report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("hard-linked", report.results[0].message)
        loader.assert_not_called()

    def test_record_family_hardlink_swap_during_validator_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            validator = root / "tools" / "validate_official_document_coverage.py"
            validator.write_text(
                "import os\n"
                "from pathlib import Path\n"
                "root = Path.cwd()\n"
                "pack = root / 'skills/source-skill/references/official-source-pack'\n"
                "for index, name in enumerate(('corpus.json', 'slices.json')):\n"
                "    original = pack / name\n"
                "    external = root / f'external-{index}.json'\n"
                "    external.write_bytes(original.read_bytes())\n"
                "    original.unlink()\n"
                "    os.link(external, original)\n"
                "raise SystemExit(0)\n",
                encoding="utf-8",
            )
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("aliased", report.results[0].message)

    def test_registration_identity_and_safe_relative_paths_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            mismatch_pack = self.make_bundle(
                root,
                index_overrides={"skill_id": "different-skill"},
            )
            mismatch = bundle_audit.audit_repository(root)
            self.assertEqual(mismatch.results[0].state, "invalid")
            self.assertIn("skill_id", mismatch.results[0].message)

            unsafe_records = {
                "corpora": ["../outside.json"],
                "slice_manifests": ["slices.json"],
                "scope_inventory": "scope-inventory.json",
                "coverage": "coverage.json",
            }
            self.make_bundle(root, index_overrides={"records": unsafe_records})
            unsafe = bundle_audit.audit_repository(root)
            self.assertEqual(unsafe.results[0].state, "invalid")
            self.assertIn("relative", unsafe.results[0].message)
            self.assertTrue(mismatch_pack.is_dir())

    def test_control_characters_cannot_inject_fake_report_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            unsafe_records = {
                "corpora": ["corpus.json"],
                "slice_manifests": ["slices.json"],
                "scope_inventory": "scope-inventory.json",
                "coverage": "missing.json\nOFFICIAL_DOC_BUNDLE SUMMARY complete=999",
            }
            self.make_bundle(root, index_overrides={"records": unsafe_records})
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertNotIn("\n", report.results[0].message)
        self.assertNotIn("complete=999", report.results[0].message)

    def test_cross_skill_record_copy_cannot_satisfy_another_skill_pack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(
                directory,
                registered_skills=("source-skill", "second-skill"),
            )
            first = self.make_bundle(root, skill_id="source-skill")
            second = self.make_bundle(root, skill_id="second-skill")
            for filename in ("scope-inventory.json", "coverage.json"):
                shutil.copyfile(first / filename, second / filename)
            report = bundle_audit.audit_repository(root)

        by_skill = {result.skill_id: result for result in report.results}
        self.assertEqual(by_skill["source-skill"].state, "complete")
        self.assertEqual(by_skill["second-skill"].state, "invalid")
        self.assertIn("skill_id", by_skill["second-skill"].message)

    def test_symlinked_reference_ancestor_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            references = root / "skills" / "source-skill" / "references"
            external = root / "external-references"
            references.rename(external)
            references.symlink_to(external, target_is_directory=True)
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("aliased", report.results[0].message)

    def test_non_string_registry_key_is_invalid_not_a_sort_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            registry = root / "registry" / "skill-registry.yaml"
            registry.write_text(
                registry.read_text(encoding="utf-8")
                + "  7:\n    lifecycle: planned\n    path: null\n",
                encoding="utf-8",
            )
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("identifier", report.results[0].message)

    def test_pack_walk_errors_fail_closed_instead_of_skipping_subtrees(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)

            def denied_walk(*args, **kwargs):
                onerror = kwargs.get("onerror")
                self.assertIsNotNone(onerror)
                onerror(PermissionError("simulated unreadable directory"))
                return ()

            with mock.patch.object(bundle_audit.os, "walk", side_effect=denied_walk):
                report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("unreadable", report.results[0].message)

    def test_explicit_external_validator_path_is_executed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            external_validator = Path(directory).parent / (
                Path(directory).name + "-external-validator.py"
            )
            try:
                external_validator.write_text(
                    "raise SystemExit(0)\n",
                    encoding="utf-8",
                )
                report = bundle_audit.audit_repository(
                    root,
                    validator_path=external_validator,
                )
            finally:
                external_validator.unlink(missing_ok=True)

        self.assertEqual(report.results[0].state, "complete")

    def test_black_box_validator_exit_zero_and_three_map_to_complete_and_partial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)

            complete = bundle_audit.audit_repository(root)
            self.assertEqual(complete.results[0].state, "complete")

            (root / "tools" / "validator-exit").write_text("3", encoding="utf-8")
            partial = bundle_audit.audit_repository(root)
            self.assertEqual(partial.results[0].state, "partial")
            self.assertEqual(bundle_audit.exit_code(partial, strict_release=False), 0)
            self.assertEqual(bundle_audit.exit_code(partial, strict_release=True), 3)

    def test_bundle_audit_requests_the_global_pack_closure_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            validator = (
                root / "tools" / "validate_official_document_coverage.py"
            )
            validator.write_text(
                "import sys\n"
                "required = '--enforce-canonical-pack-closure'\n"
                "raise SystemExit(0 if required in sys.argv else 2)\n",
                encoding="utf-8",
            )
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "complete")

    def test_global_pack_closure_nonzero_is_propagated_as_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            validator = (
                root / "tools" / "validate_official_document_coverage.py"
            )
            validator.write_text(
                "import sys\n"
                "if '--enforce-canonical-pack-closure' in sys.argv:\n"
                "    print('ERROR GLOBAL_PACK_BINDING_SET_MISMATCH canonical-packs: forged pair', file=sys.stderr)\n"
                "else:\n"
                "    print('ERROR GLOBAL_GATE_NOT_REQUESTED canonical-packs: missing flag', file=sys.stderr)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn(
            "GLOBAL_PACK_BINDING_SET_MISMATCH",
            report.results[0].message,
        )
        self.assertNotIn("GLOBAL_GATE_NOT_REQUESTED", report.results[0].message)

    def test_constructed_validator_command_uses_contract_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            (source_skill,) = bundle_audit._load_source_skills(root)
            registration = bundle_audit._load_registration(
                source_skill,
                root / "skills" / "source-skill" / "references" / "official-source-pack",
            )
            command = bundle_audit._validator_command(
                registration,
                root=root,
                validator_path=root / "tools" / "validate_official_document_coverage.py",
                python_executable=sys.executable,
            )

        self.assertEqual(
            command,
            (
                sys.executable,
                "tools/validate_official_document_coverage.py",
                "--corpus",
                "skills/source-skill/references/official-source-pack/corpus.json",
                "--slices",
                "skills/source-skill/references/official-source-pack/slices.json",
                "--scope-inventory",
                "skills/source-skill/references/official-source-pack/scope-inventory.json",
                "--coverage",
                "skills/source-skill/references/official-source-pack/coverage.json",
                "--source-root",
                ".",
                "--enforce-canonical-pack-closure",
            ),
        )

    def test_unexpected_or_invalid_validator_exit_is_invalid_in_all_modes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            self.make_bundle(root)
            (root / "tools" / "validate_official_document_coverage.py").write_text(
                "import sys\n"
                "print('ERROR FIXTURE_INVALID coverage: deliberately broken', file=sys.stderr)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            report = bundle_audit.audit_repository(root)

        self.assertEqual(report.results[0].state, "invalid")
        self.assertIn("FIXTURE_INVALID", report.results[0].message)
        self.assertEqual(bundle_audit.exit_code(report, strict_release=False), 2)
        self.assertEqual(bundle_audit.exit_code(report, strict_release=True), 2)

    def test_baseline_delta_rejects_pack_deletion_and_expectation_downgrade(self) -> None:
        baseline = bundle_audit.MigrationSnapshot(
            source_skill_ids=frozenset({"source-skill"}),
            expectations={"source-skill": "pack-required"},
            pack_skill_ids=frozenset({"source-skill"}),
        )
        downgraded = bundle_audit.MigrationSnapshot(
            source_skill_ids=frozenset({"source-skill"}),
            expectations={"source-skill": "legacy-missing"},
            pack_skill_ids=frozenset(),
        )
        findings = bundle_audit.migration_delta_findings(baseline, downgraded)

        self.assertTrue(any("cannot downgrade" in finding for finding in findings))
        self.assertTrue(any("was deleted" in finding for finding in findings))

    def test_baseline_delta_requires_new_skills_to_add_a_required_pack(self) -> None:
        baseline = bundle_audit.MigrationSnapshot(
            source_skill_ids=frozenset({"source-skill"}),
            expectations={"source-skill": "legacy-missing"},
            pack_skill_ids=frozenset(),
        )
        missing_new_pack = bundle_audit.MigrationSnapshot(
            source_skill_ids=frozenset({"source-skill", "new-skill"}),
            expectations={
                "source-skill": "legacy-missing",
                "new-skill": "legacy-missing",
            },
            pack_skill_ids=frozenset(),
        )
        promoted = bundle_audit.MigrationSnapshot(
            source_skill_ids=frozenset({"source-skill", "new-skill"}),
            expectations={
                "source-skill": "pack-required",
                "new-skill": "pack-required",
            },
            pack_skill_ids=frozenset({"source-skill", "new-skill"}),
        )

        self.assertTrue(
            bundle_audit.migration_delta_findings(baseline, missing_new_pack)
        )
        self.assertEqual(
            bundle_audit.migration_delta_findings(baseline, promoted),
            (),
        )

    def test_cli_baseline_ref_rejects_same_change_pack_delete_and_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_repository(directory)
            pack = self.make_bundle(root)
            for arguments in (
                ("init", "-q"),
                ("config", "user.name", "Bundle Test"),
                ("config", "user.email", "bundle-test@example.invalid"),
                ("add", "."),
                ("commit", "-qm", "pack-required baseline"),
            ):
                completed = subprocess.run(
                    ("git", "-C", str(root), *arguments),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
            shutil.rmtree(pack)
            self.set_expectation(root, "source-skill", "legacy-missing")

            completed = subprocess.run(
                (
                    sys.executable,
                    str(ROOT / "tools" / "validate_official_document_bundles.py"),
                    "--root",
                    str(root),
                    "--baseline-ref",
                    "HEAD",
                ),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertIn("MIGRATION_NON_MONOTONIC", completed.stderr)
        self.assertIn("cannot downgrade", completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
