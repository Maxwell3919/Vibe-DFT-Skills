from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_official_document_storage as storage_gate  # noqa: E402


AUTHORITY_REGISTRY = "registry/official-source-authorities.yaml"
CP2K_ARTIFACT = (
    "skills/cp2k-rigorous-calculations/references/"
    "official-manual/CP2K_INPUT.html"
)
CP2K_NEW_ARTIFACT = (
    "skills/cp2k-rigorous-calculations/references/"
    "official-manual/NEW_PAGE.html"
)
CP2K_CONTROL = (
    "skills/cp2k-rigorous-calculations/references/"
    "official-source-policy.md"
)
LOCAL_CONTROLS = (
    ("cp2k", CP2K_CONTROL),
    (
        "siesta",
        "skills/siesta-rigorous-calculations/references/"
        "official-artifact-fixtures.json",
    ),
    (
        "siesta",
        "skills/siesta-rigorous-calculations/references/"
        "official-artifact-forward-tests.md",
    ),
    (
        "siesta",
        "skills/siesta-rigorous-calculations/references/official-sources.md",
    ),
)
STORAGE_NAMESPACE_PREFIXES = tuple(
    prefix
    for _, (_, prefix) in sorted(storage_gate.REQUIRED_NAMESPACES.items())
)
SOURCE_PACK_SEGMENT = "/references/official-source-pack/"


def _artifact_specs(
    *,
    reclassify_cp2k_control: bool,
) -> tuple[
    tuple[str, str, tuple[str, ...], tuple[tuple[str, str], ...]],
    ...,
]:
    cp2k_registry_path = (
        CP2K_CONTROL
        if reclassify_cp2k_control
        else (
            "skills/cp2k-rigorous-calculations/references/"
            "official-source-registry.json"
        )
    )
    return (
        (
            "qe-legacy",
            "qe",
            ("qe-official-docs", "qe-release-source-docs"),
            (
                (
                    "prefix",
                    "skills/qe-rigorous-calculations/references/official-",
                ),
            ),
        ),
        (
            "vasp-wiki",
            "vasp",
            ("vasp-official-wiki",),
            (
                (
                    "prefix",
                    "skills/vasp-rigorous-calculations/references/official-",
                ),
            ),
        ),
        (
            "cp2k-manual",
            "cp2k",
            ("cp2k-official-manual",),
            (
                (
                    "prefix",
                    "skills/cp2k-rigorous-calculations/references/"
                    "official-manual/",
                ),
            ),
        ),
        (
            "cp2k-source-registry",
            "cp2k",
            ("cp2k-official-manual", "cp2k-release-source-docs"),
            (("exact", cp2k_registry_path),),
        ),
        (
            "siesta-portal-registry",
            "siesta",
            ("siesta-official-docs",),
            (
                (
                    "exact",
                    "skills/siesta-rigorous-calculations/references/"
                    "official-source-registry.json",
                ),
            ),
        ),
        (
            "siesta-release-derived",
            "siesta",
            ("siesta-release-source-docs",),
            (
                (
                    "exact",
                    "skills/siesta-rigorous-calculations/references/"
                    "official-fdf-index.json",
                ),
                (
                    "exact",
                    "skills/siesta-rigorous-calculations/references/"
                    "official-source-supplements.json",
                ),
            ),
        ),
    )


def _matches(
    path: str,
    selectors: tuple[tuple[str, str], ...],
) -> bool:
    return any(
        path == value if kind == "exact" else path.startswith(value)
        for kind, value in selectors
    )


def _digest(blobs: tuple[storage_gate.TrackedBlob, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(storage_gate.DIGEST_DOMAIN)
    for blob in sorted(blobs, key=lambda item: item.path):
        for value in (
            blob.path.encode("utf-8"),
            blob.mode.encode("ascii"),
            blob.oid.encode("ascii"),
        ):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
        digest.update(blob.size.to_bytes(8, "big"))
    return digest.hexdigest()


def _is_storage_namespace_path(path: str) -> bool:
    return (
        path.startswith(STORAGE_NAMESPACE_PREFIXES)
        and SOURCE_PACK_SEGMENT not in f"/{path}"
    )


def _worktree_blobs(root: Path) -> tuple[storage_gate.TrackedBlob, ...]:
    """Model the expected current snapshot without requiring staged changes."""

    tracked_paths = {blob.path for blob in storage_gate.load_git_index(root)}
    candidates = {
        path
        for path in tracked_paths
        if _is_storage_namespace_path(path)
        and root.joinpath(*path.split("/")).is_file()
    }
    skills_root = root / "skills"
    if skills_root.is_dir():
        for candidate in skills_root.rglob("*"):
            if not candidate.is_file():
                continue
            relative = candidate.relative_to(root).as_posix()
            if _is_storage_namespace_path(relative):
                candidates.add(relative)

    blobs: list[storage_gate.TrackedBlob] = []
    for relative in sorted(candidates):
        path = root.joinpath(*relative.split("/"))
        completed = subprocess.run(
            ("git", "-C", str(root), "hash-object", "--", relative),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        blobs.append(
            storage_gate.TrackedBlob(
                path=relative,
                mode=mode,
                oid=completed.stdout.strip(),
                size=path.stat().st_size,
            )
        )
    return tuple(blobs)


def _configuration_text(
    blobs: tuple[storage_gate.TrackedBlob, ...],
    *,
    authority_registry: str = AUTHORITY_REGISTRY,
    reclassify_cp2k_control: bool = False,
) -> str:
    specs = _artifact_specs(
        reclassify_cp2k_control=reclassify_cp2k_control,
    )
    lines = [
        'schema_version: "1.0"',
        f"authority_registry: {authority_registry}",
        "migration_policy:",
        "  authority_evaluation: all-of",
        "  waiver_policy: forbidden",
        "  unclassified_namespace_path: invalid",
        "  baseline_policy: exact-git-index",
        "",
        "namespaces:",
        "  qe:",
        "    provider_id: qe",
        (
            "    path_prefix: "
            "skills/qe-rigorous-calculations/references/official-"
        ),
        "  vasp:",
        "    provider_id: vasp",
        (
            "    path_prefix: "
            "skills/vasp-rigorous-calculations/references/official-"
        ),
        "  cp2k:",
        "    provider_id: cp2k",
        (
            "    path_prefix: "
            "skills/cp2k-rigorous-calculations/references/official-"
        ),
        "  siesta:",
        "    provider_id: siesta",
        (
            "    path_prefix: "
            "skills/siesta-rigorous-calculations/references/official-"
        ),
        "",
        "artifact_sets:",
    ]
    for set_id, provider_id, authority_ids, selectors in specs:
        selected = tuple(blob for blob in blobs if _matches(blob.path, selectors))
        lines.extend(
            (
                f"  {set_id}:",
                f"    provider_id: {provider_id}",
                f"    authority_ids: [{', '.join(authority_ids)}]",
                "    selectors:",
            )
        )
        for kind, value in selectors:
            lines.append(f"      - {{kind: {kind}, value: {value}}}")
        lines.extend(
            (
                "    baseline:",
                f"      path_count: {len(selected)}",
                f"      byte_count: {sum(blob.size for blob in selected)}",
                f"      digest_sha256: {_digest(selected)}",
            )
        )
    controls = [
        (provider_id, path)
        for provider_id, path in LOCAL_CONTROLS
        if not (reclassify_cp2k_control and path == CP2K_CONTROL)
    ]
    lines.extend(("", "local_controls:"))
    blobs_by_path = {blob.path: blob for blob in blobs}
    for provider_id, path in controls:
        blob = blobs_by_path.get(path)
        mode = blob.mode if blob is not None else "100644"
        byte_count = blob.size if blob is not None else 0
        blob_oid = blob.oid if blob is not None else "0" * 40
        lines.extend(
            (
                f"  - provider_id: {provider_id}",
                f"    path: {path}",
                (
                    "    baseline: "
                    f'{{mode: "{mode}", byte_count: {byte_count}, '
                    f"blob_oid: {blob_oid}}}"
                ),
            )
        )
    return "\n".join(lines) + "\n"


def _authorities() -> dict[str, dict[str, str]]:
    return {
        "qe-official-docs": {
            "provider_id": "qe",
            "bundle_content_policy": "forbidden",
        },
        "qe-release-source-docs": {
            "provider_id": "qe",
            "bundle_content_policy": "forbidden",
        },
        "vasp-official-wiki": {
            "provider_id": "vasp",
            "bundle_content_policy": "forbidden",
        },
        "cp2k-official-manual": {
            "provider_id": "cp2k",
            "bundle_content_policy": "forbidden",
        },
        "cp2k-release-source-docs": {
            "provider_id": "cp2k",
            "bundle_content_policy": "forbidden",
        },
        "siesta-official-docs": {
            "provider_id": "siesta",
            "bundle_content_policy": "forbidden",
        },
        "siesta-release-source-docs": {
            "provider_id": "siesta",
            "bundle_content_policy": "forbidden",
        },
    }


class OfficialDocumentStorageMigrationTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ("git", "-C", str(root), *arguments),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )
        return completed

    def write_file(self, root: Path, relative: str, content: str) -> Path:
        path = root.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def rewrite_current_baselines(
        self,
        root: Path,
        *,
        reclassify_cp2k_control: bool = False,
        stage: bool = False,
    ) -> None:
        blobs = _worktree_blobs(root)
        configuration = _configuration_text(
            blobs,
            reclassify_cp2k_control=reclassify_cp2k_control,
        )
        self.write_file(
            root,
            "registry/official-document-storage-discovery.yaml",
            configuration,
        )
        if stage:
            self.git(
                root,
                "add",
                "registry/official-document-storage-discovery.yaml",
            )

    def current_report(self, root: Path) -> storage_gate.StorageReport:
        return storage_gate.evaluate_storage(
            _worktree_blobs(root),
            storage_gate.load_configuration(root),
            _authorities(),
            enforce_baseline=True,
        )

    def assert_no_staged_current_change(self, root: Path) -> None:
        self.git(root, "diff", "--cached", "--quiet")

    @contextmanager
    def repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.git(root, "init", "-q")
            self.git(root, "config", "user.name", "Storage Migration Test")
            self.git(
                root,
                "config",
                "user.email",
                "storage-migration@example.invalid",
            )
            self.git(root, "config", "core.filemode", "true")
            self.write_file(root, CP2K_ARTIFACT, "baseline manual page\n")
            for _, control_path in LOCAL_CONTROLS:
                self.write_file(root, control_path, "local control\n")
            self.git(root, "add", "skills")
            self.rewrite_current_baselines(root, stage=True)
            initial_report = self.current_report(root)
            self.assertEqual(initial_report.invalid_findings, ())
            self.assertEqual(initial_report.release_blocking_path_count, 1)
            self.git(root, "commit", "-qm", "storage migration baseline")
            yield root

    def assert_non_monotonic(self, root: Path, expected_path: str) -> None:
        findings = storage_gate.validate_migration_delta(root, "HEAD")
        self.assertTrue(findings)
        self.assertIn(expected_path, "\n".join(findings))

    def test_artifact_addition_cannot_be_hidden_by_updating_current_baseline(
        self,
    ) -> None:
        with self.repository() as root:
            self.write_file(root, CP2K_NEW_ARTIFACT, "new manual page\n")
            self.rewrite_current_baselines(root)

            self.assert_no_staged_current_change(root)
            current = self.current_report(root)
            self.assertEqual(current.invalid_findings, ())
            self.assertEqual(current.release_blocking_path_count, 2)
            self.assert_non_monotonic(root, CP2K_NEW_ARTIFACT)

    def test_artifact_blob_rewrite_cannot_be_hidden_by_updating_digest(
        self,
    ) -> None:
        with self.repository() as root:
            self.write_file(root, CP2K_ARTIFACT, "rewritten manual page\n")
            self.rewrite_current_baselines(root)

            self.assert_no_staged_current_change(root)
            current = self.current_report(root)
            self.assertEqual(current.invalid_findings, ())
            self.assert_non_monotonic(root, CP2K_ARTIFACT)

    def test_artifact_mode_rewrite_cannot_be_hidden_by_updating_digest(
        self,
    ) -> None:
        with self.repository() as root:
            artifact = root.joinpath(*CP2K_ARTIFACT.split("/"))
            os.chmod(artifact, artifact.stat().st_mode | 0o111)
            self.rewrite_current_baselines(root)

            self.assert_no_staged_current_change(root)
            current = self.current_report(root)
            self.assertEqual(current.invalid_findings, ())
            self.assert_non_monotonic(root, CP2K_ARTIFACT)

    def test_artifact_deletion_with_exact_current_baseline_is_monotonic(
        self,
    ) -> None:
        with self.repository() as root:
            (root / CP2K_ARTIFACT).unlink()
            self.rewrite_current_baselines(root)

            self.assert_no_staged_current_change(root)
            current = self.current_report(root)
            self.assertEqual(current.invalid_findings, ())
            self.assertEqual(current.release_blocking_path_count, 0)
            self.assertEqual(
                storage_gate.validate_migration_delta(root, "HEAD"),
                (),
            )

    def test_local_control_content_or_mode_rewrite_is_non_monotonic(
        self,
    ) -> None:
        changes = (
            (
                "content",
                lambda root: self.write_file(
                    root,
                    CP2K_CONTROL,
                    "rewritten control\n",
                ),
            ),
            (
                "mode",
                lambda root: os.chmod(
                    root.joinpath(*CP2K_CONTROL.split("/")),
                    root.joinpath(*CP2K_CONTROL.split("/")).stat().st_mode
                    | 0o111,
                ),
            ),
        )
        for label, change in changes:
            with self.subTest(change=label), self.repository() as root:
                change(root)
                self.rewrite_current_baselines(root)
                self.assert_no_staged_current_change(root)
                current = self.current_report(root)
                self.assertEqual(current.invalid_findings, ())
                self.assert_non_monotonic(root, CP2K_CONTROL)

    def test_local_control_cannot_be_reclassified_as_an_artifact(self) -> None:
        with self.repository() as root:
            self.rewrite_current_baselines(
                root,
                reclassify_cp2k_control=True,
            )

            self.assert_no_staged_current_change(root)
            current = self.current_report(root)
            self.assertEqual(current.invalid_findings, ())
            self.assertEqual(current.local_control_count, 3)
            self.assertEqual(current.release_blocking_path_count, 2)
            self.assert_non_monotonic(root, CP2K_CONTROL)

    def test_canonical_source_pack_is_outside_storage_migration(self) -> None:
        pack_record = (
            "skills/cp2k-rigorous-calculations/references/"
            "official-source-pack/corpora/manual.json"
        )
        with self.repository() as root:
            self.write_file(root, pack_record, '{"schema_version":"1.0"}\n')

            self.assert_no_staged_current_change(root)
            current = self.current_report(root)
            self.assertEqual(current.invalid_findings, ())
            self.assertEqual(current.release_blocking_path_count, 1)
            self.assertEqual(
                storage_gate.validate_migration_delta(root, "HEAD"),
                (),
            )

    def test_authority_registry_cannot_redirect_to_a_forged_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(
                root,
                "registry/official-document-storage-discovery.yaml",
                _configuration_text(
                    (),
                    authority_registry="registry/forged-authorities.yaml",
                ),
            )
            self.write_file(
                root,
                "registry/forged-authorities.yaml",
                'schema_version: "1.0"\nauthorities: {}\n',
            )

            with self.assertRaises(storage_gate.StorageAuditError) as raised:
                storage_gate.load_configuration(root)

        self.assertIn("authority_registry", str(raised.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
