from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_official_document_storage as storage_gate  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402


class OfficialDocumentStorageGateTests(unittest.TestCase):
    @staticmethod
    def git_blob_oid(raw: bytes) -> str:
        digest = hashlib.sha1()
        digest.update(f"blob {len(raw)}\0".encode("ascii"))
        digest.update(raw)
        return digest.hexdigest()

    def test_live_worktree_is_identity_valid_but_requires_v11_migration(self) -> None:
        report = storage_gate.audit_repository(ROOT)

        self.assertEqual(report.invalid_findings, ())
        self.assertEqual(report.namespace_path_count, 2079)
        self.assertEqual(report.artifact_path_count, 2075)
        self.assertEqual(report.local_control_count, 4)
        self.assertEqual(report.local_control_bytes, 11_983)
        self.assertEqual(
            report.local_control_digest_sha256,
            "6a2ddf8a50f03111d8ca246801ef0faca1666ed50af05b989a759bfc06f28b3e",
        )
        self.assertEqual(report.artifact_bytes, 18_950_704)
        self.assertEqual(report.forbidden_path_count, 2075)
        self.assertEqual(report.release_blocking_path_count, 2075)
        self.assertEqual(report.worktree_drift_findings, ())
        self.assertEqual(storage_gate.exit_code(report, strict_release=False), 0)
        self.assertEqual(storage_gate.exit_code(report, strict_release=True), 3)
        self.assertEqual(
            {result.state for result in report.artifact_sets},
            {"legacy-technical-migration-required"},
        )

    def test_unclassified_new_official_index_path_is_invalid_not_grandfathered(self) -> None:
        configuration = storage_gate.load_configuration(ROOT)
        authorities = storage_gate.load_authority_projection(ROOT)
        blobs = list(
            storage_gate.load_worktree_view(
                ROOT,
                storage_gate.load_git_index(ROOT),
                configuration,
            ).blobs
        )
        blobs.append(
            storage_gate.TrackedBlob(
                path=(
                    "skills/cp2k-rigorous-calculations/references/"
                    "official-new-content.txt"
                ),
                mode="100644",
                oid="0" * 40,
                size=17,
            )
        )

        report = storage_gate.evaluate_storage(
            tuple(blobs),
            configuration,
            authorities,
            enforce_baseline=False,
        )

        self.assertTrue(
            any("unclassified" in finding for finding in report.invalid_findings)
        )
        self.assertEqual(storage_gate.exit_code(report, strict_release=False), 2)

    def test_same_provider_authorities_are_all_of_and_cannot_overwrite_each_other(self) -> None:
        configuration = storage_gate.load_configuration(ROOT)
        authorities = copy.deepcopy(storage_gate.load_authority_projection(ROOT))
        authorities["qe-release-source-docs"]["bundle_content_policy"] = object()
        qe_blob = next(
            blob
            for blob in storage_gate.load_git_index(ROOT)
            if blob.path.startswith(
                "skills/qe-rigorous-calculations/references/official-"
            )
        )

        report = storage_gate.evaluate_storage(
            (qe_blob,),
            configuration,
            authorities,
            enforce_baseline=False,
        )

        self.assertEqual(report.invalid_findings, ())
        self.assertEqual(report.forbidden_path_count, 1)
        qe_set = next(item for item in report.artifact_sets if item.set_id == "qe-legacy")
        self.assertEqual(
            qe_set.authority_ids,
            ("qe-official-docs", "qe-release-source-docs"),
        )
        self.assertEqual(qe_set.state, "legacy-technical-migration-required")

    def test_unknown_or_provider_mismatched_authority_is_invalid(self) -> None:
        configuration = storage_gate.load_configuration(ROOT)
        authorities = copy.deepcopy(storage_gate.load_authority_projection(ROOT))
        authorities["qe-official-docs"]["provider_id"] = "vasp"
        qe_blob = next(
            blob
            for blob in storage_gate.load_git_index(ROOT)
            if blob.path.startswith(
                "skills/qe-rigorous-calculations/references/official-"
            )
        )

        report = storage_gate.evaluate_storage(
            (qe_blob,),
            configuration,
            authorities,
            enforce_baseline=False,
        )

        self.assertTrue(
            any("provider" in finding for finding in report.invalid_findings)
        )

    def test_canonical_pack_domain_is_excluded_but_adjacent_names_are_not(self) -> None:
        configuration = storage_gate.load_configuration(ROOT)
        authorities = storage_gate.load_authority_projection(ROOT)
        blobs = list(
            storage_gate.load_worktree_view(
                ROOT,
                storage_gate.load_git_index(ROOT),
                configuration,
            ).blobs
        )
        pack_records = (
            storage_gate.TrackedBlob(
                path=(
                    "skills/qe-rigorous-calculations/references/"
                    "official-source-pack/bundle.json"
                ),
                mode="100644",
                oid="1" * 40,
                size=101,
            ),
            storage_gate.TrackedBlob(
                path=(
                    "skills/qe-rigorous-calculations/references/"
                    "official-source-pack/corpus.json"
                ),
                mode="100644",
                oid="2" * 40,
                size=202,
            ),
        )
        delegated = storage_gate.evaluate_storage(
            tuple([*blobs, *pack_records]),
            configuration,
            authorities,
            enforce_baseline=True,
        )
        self.assertEqual(delegated.invalid_findings, ())
        self.assertEqual(delegated.artifact_path_count, 2075)
        self.assertEqual(delegated.artifact_bytes, 18_950_704)

        adjacent = storage_gate.evaluate_storage(
            tuple(
                [
                    *blobs,
                    storage_gate.TrackedBlob(
                        path=(
                            "skills/qe-rigorous-calculations/references/"
                            "official-source-pack-copy/payload.json"
                        ),
                        mode="100644",
                        oid="3" * 40,
                        size=303,
                    ),
                ]
            ),
            configuration,
            authorities,
            enforce_baseline=True,
        )
        self.assertTrue(adjacent.invalid_findings)
        self.assertEqual(storage_gate.exit_code(adjacent, strict_release=False), 2)

    def test_authority_registry_path_is_fixed_to_the_canonical_registry(self) -> None:
        data = load_yaml_strict(
            ROOT / "registry" / "official-document-storage-discovery.yaml",
            "official-document-storage-discovery.yaml",
        )
        data["authority_registry"] = "registry/forged-authorities.yaml"

        with self.assertRaisesRegex(
            storage_gate.StorageAuditError,
            "authority_registry",
        ):
            storage_gate._parse_configuration(data)

    def test_local_control_identity_is_exact_not_a_payload_escape_lane(self) -> None:
        configuration = storage_gate.load_configuration(ROOT)
        authorities = storage_gate.load_authority_projection(ROOT)
        blobs = list(storage_gate.load_git_index(ROOT))
        target = (
            "skills/cp2k-rigorous-calculations/references/"
            "official-source-policy.md"
        )
        modified = tuple(
            replace(
                blob,
                oid="f" * 40,
                size=blob.size + 4096,
            )
            if blob.path == target
            else blob
            for blob in blobs
        )

        report = storage_gate.evaluate_storage(
            modified,
            configuration,
            authorities,
            enforce_baseline=True,
        )

        self.assertTrue(
            any(
                "local control" in finding and "identity" in finding
                for finding in report.invalid_findings
            )
        )
        self.assertEqual(storage_gate.exit_code(report, strict_release=False), 2)

    def test_worktree_view_surfaces_modified_deleted_symlink_and_untracked_paths(
        self,
    ) -> None:
        configuration = storage_gate.load_configuration(ROOT)
        relative = (
            "skills/qe-rigorous-calculations/references/official-fixture.json"
        )
        original = b'{"state":"original"}\n'
        tracked = storage_gate.TrackedBlob(
            path=relative,
            mode="100644",
            oid=self.git_blob_oid(original),
            size=len(original),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True)
            path.write_bytes(original)
            clean = storage_gate.load_worktree_view(
                root,
                (tracked,),
                configuration,
            )
            self.assertEqual(clean.invalid_findings, ())
            self.assertEqual(clean.drift_findings, ())

            path.write_bytes(b'{"state":"modified"}\n')
            modified = storage_gate.load_worktree_view(
                root,
                (tracked,),
                configuration,
            )
            self.assertEqual(modified.invalid_findings, ())
            self.assertTrue(any(relative in item for item in modified.drift_findings))

            path.unlink()
            deleted = storage_gate.load_worktree_view(
                root,
                (tracked,),
                configuration,
            )
            self.assertTrue(any("deleted" in item for item in deleted.drift_findings))

            target = root / "outside.json"
            target.write_bytes(original)
            path.symlink_to(target)
            symlinked = storage_gate.load_worktree_view(
                root,
                (tracked,),
                configuration,
            )
            self.assertTrue(any("unsafe" in item for item in symlinked.invalid_findings))
            path.unlink()

            untracked_path = path.with_name("official-untracked.json")
            untracked_path.write_bytes(b"{}\n")
            untracked = storage_gate.load_worktree_view(
                root,
                (),
                configuration,
            )
            self.assertTrue(
                any("untracked" in item for item in untracked.invalid_findings)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
