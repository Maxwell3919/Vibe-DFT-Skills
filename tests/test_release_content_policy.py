from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import release_content_policy as policy  # noqa: E402


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _codes(findings: tuple[policy.Finding, ...]) -> set[str]:
    return {finding.code for finding in findings}


class ReleaseContentPolicyTests(unittest.TestCase):
    def test_public_interface_and_fixed_vocabularies_are_stable(self) -> None:
        self.assertTrue(sys.dont_write_bytecode)
        self.assertEqual(
            policy.ROLES,
            frozenset(
                {
                    "repository-source",
                    "test-source",
                    "schema",
                    "structured-record",
                    "canonical-pack-metadata",
                    "official-document-body",
                    "repository-public-asset",
                    "synthetic-scientific-fixture",
                    "calculation-payload",
                    "opaque-binary",
                }
            ),
        )
        self.assertEqual(
            {
                policy.CREDENTIAL_FILE,
                policy.PRIVATE_KEY,
                policy.PROVIDER_TOKEN,
                policy.CREDENTIAL_ASSIGNMENT,
                policy.PRIVATE_HOME,
                policy.RESTRICTED_POTENTIAL_PATH,
                policy.RESTRICTED_POTENTIAL_CONTENT,
                policy.RUNTIME_ARTIFACT,
                policy.NESTED_ARCHIVE,
                policy.OPAQUE_BINARY_UNREVIEWED,
            },
            {
                "credential-file",
                "private-key",
                "provider-token",
                "credential-assignment",
                "private-home",
                "restricted-potential-path",
                "restricted-potential-content",
                "runtime-artifact",
                "nested-archive",
                "opaque-binary-unreviewed",
            },
        )

    def test_finding_is_frozen_orderable_and_serializes_without_message_text(self) -> None:
        first = policy.Finding(
            "credential-file",
            "blocker",
            "repository",
            "repository-source",
            ".env",
            "0" * 64,
            "",
            "",
            "RCP-PATH-002",
        )
        second = policy.Finding(
            "runtime-artifact",
            "blocker",
            "repository",
            "repository-source",
            "cache.pyc",
            "1" * 64,
            "",
            "",
            "RCP-PATH-007",
        )
        self.assertEqual(sorted((second, first)), [first, second])
        with self.assertRaises(FrozenInstanceError):
            first.code = "changed"  # type: ignore[misc]
        self.assertEqual(
            first.as_dict(),
            {
                "code": "credential-file",
                "severity": "blocker",
                "scope": "repository",
                "role": "repository-source",
                "path": ".env",
                "path_sha256": "0" * 64,
                "file_sha256": "",
                "blob_oid": "",
                "rule_id": "RCP-PATH-002",
            },
        )
        self.assertNotIn("message", first.as_dict())
        self.assertNotIn("context", first.as_dict())

    def test_classify_path_covers_every_role(self) -> None:
        cases = {
            "tools/check.py": "repository-source",
            "tests/test_check.py": "test-source",
            "contracts/run.schema.json": "schema",
            "registry/skill-registry.yaml": "structured-record",
            (
                "skills/qe/references/official-source-pack/"
                "official-source-pack.json"
            ): "canonical-pack-metadata",
            (
                "skills/qe/references/official-source-pack/content/manual.html"
            ): "official-document-body",
            (
                "skills/qe/references/official-raw/user-guide.pdf"
            ): "official-document-body",
            "docs/images/coverage.png": "repository-public-asset",
            "tests/fixtures/synthetic/run.out": "synthetic-scientific-fixture",
            "scratch/OUTCAR": "calculation-payload",
            "assets/data.bin": "opaque-binary",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(policy.classify_path(path), expected)

    def test_sanitized_forward_fixture_and_mplstyle_have_narrow_source_roles(self) -> None:
        sanitized = (
            "skills/cp2k-rigorous-calculations/references/forward-fixtures/"
            "cp2k-9.0-energy-force.sanitized.out"
        )
        style = "skills/dft-postprocess/assets/dft-publication.mplstyle"
        self.assertEqual(
            policy.classify_path(sanitized),
            "synthetic-scientific-fixture",
        )
        self.assertEqual(policy.classify_path(style), "repository-source")
        self.assertEqual(
            policy.scan_path(
                sanitized,
                "synthetic-scientific-fixture",
                "active-release",
            ),
            (),
        )
        self.assertEqual(
            policy.scan_path(style, "repository-source", "active-release"),
            (),
        )

        self.assertEqual(
            policy.classify_path(
                "skills/cp2k-rigorous-calculations/references/"
                "forward-fixtures/unsanitized.out"
            ),
            "opaque-binary",
        )
        self.assertEqual(
            policy.classify_path(
                "skills/cp2k-rigorous-calculations/references/"
                "cp2k-9.0-energy-force.sanitized.out"
            ),
            "opaque-binary",
        )

    def test_standard_text_repository_dotfiles_are_source_not_opaque(self) -> None:
        for path in (
            ".dockerignore",
            ".editorconfig",
            ".gitattributes",
            ".gitignore",
            ".gitmodules",
            ".mailmap",
            ".npmignore",
            ".github/CODEOWNERS",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    policy.classify_path(path),
                    "repository-source",
                )
                self.assertEqual(
                    policy.scan_bytes(
                        path,
                        b"safe repository configuration\n",
                        "repository-source",
                        "repository",
                        _sha256(b"safe repository configuration\n"),
                    ),
                    (),
                )

    def test_classify_path_accepts_only_bounded_official_assertions(self) -> None:
        body = "skills/qe/references/official-manual/page.html"
        metadata = (
            "skills/qe/references/official-source-pack/corpus-manifest.json"
        )
        self.assertEqual(
            policy.classify_path(body, "official-document-body"),
            "official-document-body",
        )
        self.assertEqual(
            policy.classify_path(metadata, "canonical-pack-metadata"),
            "canonical-pack-metadata",
        )
        with self.assertRaises(ValueError):
            policy.classify_path("assets/random.pdf", "official-document-body")
        with self.assertRaises(ValueError):
            policy.classify_path(body, "custom-regex-or-waiver")
        with self.assertRaises(ValueError):
            policy.classify_path(body, {"waiver": True})  # type: ignore[arg-type]

    def test_invalid_role_scope_and_hash_metadata_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            policy.scan_path("tools/a.py", "unknown", "repository")
        with self.assertRaises(ValueError):
            policy.scan_path("tools/a.py", "repository-source", "../scope")
        with self.assertRaises(ValueError):
            policy.scan_bytes(
                "tools/a.py",
                b"safe\n",
                "repository-source",
                "repository",
                "not-a-sha",
            )
        with self.assertRaises(ValueError):
            policy.scan_bytes(
                "tools/a.py",
                b"safe\n",
                "repository-source",
                "repository",
                _sha256(b"safe\n"),
                "not-an-object-id",
            )

    def test_scan_path_rejects_unsafe_paths_without_disclosing_absolute_root(self) -> None:
        local = "/" + "Users" + "/" + "real-person" + "/project/secret.txt"
        findings = policy.scan_path(local, "repository-source", "repository")
        self.assertEqual(_codes(findings), {policy.UNSAFE_PATH})
        finding = findings[0]
        self.assertEqual(finding.path, "<unsafe-path>")
        self.assertEqual(finding.path_sha256, _sha256(local.encode("utf-8")))
        self.assertNotIn("real-person", repr(finding.as_dict()))

    def test_path_checks_are_casefolded_for_credentials_and_potentials(self) -> None:
        cases = {
            "config/.EnV": policy.CREDENTIAL_FILE,
            "keys/ID_RSA": policy.PRIVATE_KEY,
            "calc/PoTcAr": policy.RESTRICTED_POTENTIAL_PATH,
            "calc/POTCAR.PBE": policy.RESTRICTED_POTENTIAL_PATH,
            "calc/Si.PsCtR": policy.RESTRICTED_POTENTIAL_PATH,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertIn(
                    expected,
                    _codes(policy.scan_path(path, "repository-source", "repository")),
                )

    def test_runtime_archive_and_calculation_payload_paths_are_blocked(self) -> None:
        cases = {
            "tools/__PyCaChE__/guard.pyc": policy.RUNTIME_ARTIFACT,
            "release/source.TAR.GZ": policy.NESTED_ARCHIVE,
            "run/OUTCAR": policy.CALCULATION_PAYLOAD_UNREVIEWED,
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertIn(
                    expected,
                    _codes(policy.scan_path(path, "repository-source", "repository")),
                )

    def test_reviewed_official_pdf_is_not_an_unreviewed_opaque_binary(self) -> None:
        path = "skills/qe/references/official-manual/user-guide.pdf"
        findings = policy.scan_path(path, "official-document-body", "repository")
        self.assertNotIn(policy.OPAQUE_BINARY_UNREVIEWED, _codes(findings))
        unreviewed = policy.scan_path(
            "assets/user-guide.pdf", "opaque-binary", "repository"
        )
        self.assertIn(policy.OPAQUE_BINARY_UNREVIEWED, _codes(unreviewed))

    def test_legacy_official_star_directory_is_provenance_neutral_body(self) -> None:
        path = (
            "skills/qe-rigorous-calculations/references/"
            "official-raw/user_guide.pdf"
        )
        self.assertEqual(policy.classify_path(path), "official-document-body")
        findings = policy.scan_path(path, "official-document-body", "repository")
        self.assertNotIn(policy.OPAQUE_BINARY_UNREVIEWED, _codes(findings))

    def test_public_docs_image_requires_matching_supported_magic(self) -> None:
        path = "docs/images/coverage.png"
        raw = b"\x89P" + b"NG\r\n\x1a\n" + b"public-image"
        self.assertEqual(policy.classify_path(path), "repository-public-asset")
        findings = policy.scan_bytes(
            path,
            raw,
            "repository-public-asset",
            "repository",
            _sha256(raw),
        )
        self.assertEqual(findings, ())

        mismatched = b"\xff\xd8\xff\xe0" + b"jpeg-image"
        mismatch_findings = policy.scan_bytes(
            path,
            mismatched,
            "repository-public-asset",
            "repository",
            _sha256(mismatched),
        )
        self.assertIn(
            policy.OPAQUE_BINARY_UNREVIEWED, _codes(mismatch_findings)
        )

    def test_executable_document_and_archive_renamed_png_are_rejected(self) -> None:
        path = "docs/images/renamed.png"
        samples = (
            b"\x7fELF" + b"\x00payload",
            b"MZ" + b"\x00payload",
            b"%PDF-" + b"1.7\n",
            b"PK\x03\x04" + b"\x00payload",
        )
        for raw in samples:
            with self.subTest(prefix=raw[:4]):
                findings = policy.scan_bytes(
                    path,
                    raw,
                    "repository-public-asset",
                    "repository",
                    _sha256(raw),
                )
                self.assertIn(
                    policy.OPAQUE_BINARY_UNREVIEWED, _codes(findings)
                )

    def test_public_image_role_does_not_waive_content_or_archive_rules(self) -> None:
        path = "docs/images/coverage.png"
        token = b"gh" + b"p_" + (b"A1b2C3d4" * 4)
        raw = b"\x89P" + b"NG\r\n\x1a\n" + token
        findings = policy.scan_bytes(
            path,
            raw,
            "repository-public-asset",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.PROVIDER_TOKEN, _codes(findings))
        self.assertNotIn(
            policy.OPAQUE_BINARY_UNREVIEWED, _codes(findings)
        )

        archived = policy.scan_path(
            "docs/images/coverage.png.zip",
            "repository-public-asset",
            "repository",
        )
        self.assertIn(policy.NESTED_ARCHIVE, _codes(archived))
        self.assertIn(policy.OPAQUE_BINARY_UNREVIEWED, _codes(archived))

    def test_private_key_requires_structural_body_and_both_delimiters(self) -> None:
        begin = b"-----BEGIN " + b"PRIVATE KEY-----"
        end = b"-----END " + b"PRIVATE KEY-----"
        raw = begin + b"\n" + (b"QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo=" * 2) + b"\n" + end
        findings = policy.scan_bytes(
            "payload.txt",
            raw,
            "structured-record",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.PRIVATE_KEY, _codes(findings))
        marker_only = b"scanner = re.compile(rb'-----BEGIN PRIVATE KEY-----')\n"
        marker_findings = policy.scan_bytes(
            "tools/scanner.py",
            marker_only,
            "repository-source",
            "repository",
            _sha256(marker_only),
        )
        self.assertNotIn(policy.PRIVATE_KEY, _codes(marker_findings))

    def test_provider_tokens_are_detected_when_assembled_at_runtime(self) -> None:
        aws = b"AK" + b"IA" + b"A1B2C3D4E5F6G7H8"
        github = b"gh" + b"p_" + (b"A1b2C3d4" * 4)
        raw = b"first=" + aws + b"\nsecond=" + github + b"\n"
        findings = policy.scan_bytes(
            "config.txt",
            raw,
            "structured-record",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.PROVIDER_TOKEN, _codes(findings))
        self.assertNotIn(aws.decode("ascii"), repr([item.as_dict() for item in findings]))
        self.assertNotIn(
            github.decode("ascii"), repr([item.as_dict() for item in findings])
        )

    def test_secret_in_path_is_redacted_but_hashed(self) -> None:
        secret = "gh" + "p_" + ("A1b2C3d4" * 4)
        path = f"scratch/{secret}.txt"
        findings = policy.scan_path(path, "repository-source", "repository")
        self.assertTrue(findings)
        self.assertTrue(all(item.path == "<redacted-path>" for item in findings))
        self.assertTrue(all(item.path_sha256 == _sha256(path.encode()) for item in findings))
        self.assertNotIn(secret, repr([item.as_dict() for item in findings]))

    def test_high_confidence_credential_assignment_is_detected(self) -> None:
        key = b"api_" + b"key"
        value = b"R4nd0mValue" * 4
        raw = key + b" = " + value + b"\n"
        findings = policy.scan_bytes(
            "settings.conf",
            raw,
            "structured-record",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.CREDENTIAL_ASSIGNMENT, _codes(findings))
        self.assertNotIn(value.decode(), repr([item.as_dict() for item in findings]))

    def test_placeholders_urls_and_scanner_definitions_do_not_false_positive(self) -> None:
        raw = (
            b"https://www.quantum-espresso.org/Doc/user_guide/node6.html\n"
            b"https://example.org/docs?api_key=example\n"
            b"password = placeholder\n"
            b"api_key = researcher\n"
            b"pattern = rb'(?:password|api[_-]?key)\\s*[:=]'\n"
            b"homes = ['/Users/example/project', '/home/researcher/run', "
            b"'/Users/alice/data', '/home/user/work']\n"
        )
        for role in ("repository-source", "test-source", "schema"):
            with self.subTest(role=role):
                findings = policy.scan_bytes(
                    "tools/scanner.py",
                    raw,
                    role,
                    "repository",
                    _sha256(raw),
                )
                self.assertFalse(
                    _codes(findings)
                    & {
                        policy.PROVIDER_TOKEN,
                        policy.CREDENTIAL_ASSIGNMENT,
                        policy.PRIVATE_HOME,
                    }
                )

    def test_real_private_home_is_detected_without_name_disclosure(self) -> None:
        name = b"actual-" + b"researcher"
        raw = b"input=" + b"/Users/" + name + b"/private/run\n"
        findings = policy.scan_bytes(
            "record.txt",
            raw,
            "structured-record",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.PRIVATE_HOME, _codes(findings))
        self.assertNotIn(name.decode(), repr([item.as_dict() for item in findings]))

    def test_potential_content_requires_multiple_line_structures(self) -> None:
        raw = (
            b"PAW_PBE synthetic 01Jan2000\n"
            b"TIT" + b"EL = PAW_PBE synthetic\n"
            b"VRH" + b"FIN = X: s2\n"
            b"POM" + b"ASS = 1.0; ZVAL = 1.0\n"
            b"End of " + b"Dataset\n"
        )
        findings = policy.scan_bytes(
            "payload.dat",
            raw,
            "calculation-payload",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.RESTRICTED_POTENTIAL_CONTENT, _codes(findings))

    def test_single_potential_markers_in_official_explanation_do_not_match(self) -> None:
        samples = (
            b"The official manual explains the TITEL = field.\n",
            b"The phrase End of Dataset terminates one illustrated block.\n",
        )
        for raw in samples:
            with self.subTest(raw=raw):
                findings = policy.scan_bytes(
                    "skills/vasp/references/official-manual/page.html",
                    raw,
                    "official-document-body",
                    "repository",
                    _sha256(raw),
                )
                self.assertNotIn(
                    policy.RESTRICTED_POTENTIAL_CONTENT, _codes(findings)
                )

    def test_scanner_source_with_all_marker_literals_is_not_potential_content(self) -> None:
        raw = (
            b"MARKERS = (b'TITEL =', b'VRHFIN =', b'POMASS =', "
            b"b'End of Dataset', b'PSCTR')\n"
        )
        findings = policy.scan_bytes(
            "tools/scanner.py",
            raw,
            "repository-source",
            "repository",
            _sha256(raw),
        )
        self.assertNotIn(policy.RESTRICTED_POTENTIAL_CONTENT, _codes(findings))

    def test_psctr_content_requires_header_and_multiple_structural_markers(self) -> None:
        raw = (
            b"PS" + b"CTR\n"
            b"Atomic " + b"number: 14\n"
            b"Valence " + b"charge: 4.0\n"
            b"Down pseudopotential " + b"follows\n"
        )
        findings = policy.scan_bytes(
            "payload.dat",
            raw,
            "calculation-payload",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.RESTRICTED_POTENTIAL_CONTENT, _codes(findings))

    def test_binary_magic_and_opaque_role_are_unreviewed(self) -> None:
        raw = b"\x89P" + b"NG\r\n\x1a\n" + b"\x00payload"
        findings = policy.scan_bytes(
            "assets/image.dat",
            raw,
            "repository-source",
            "repository",
            _sha256(raw),
        )
        self.assertIn(policy.OPAQUE_BINARY_UNREVIEWED, _codes(findings))
        text = b"plain text\n"
        role_findings = policy.scan_bytes(
            "assets/data.txt",
            text,
            "opaque-binary",
            "repository",
            _sha256(text),
        )
        self.assertIn(policy.OPAQUE_BINARY_UNREVIEWED, _codes(role_findings))

    def test_hash_mismatch_and_scan_limit_fail_closed(self) -> None:
        raw = b"safe\n"
        mismatch = policy.scan_bytes(
            "safe.txt",
            raw,
            "repository-source",
            "repository",
            "0" * 64,
        )
        self.assertIn(policy.FILE_SHA256_MISMATCH, _codes(mismatch))
        oversized = b"x" * (policy.MAX_SCAN_BYTES + 1)
        limited = policy.scan_bytes(
            "large.txt",
            oversized,
            "repository-source",
            "repository",
            _sha256(oversized),
        )
        self.assertIn(policy.SCAN_LIMIT_EXCEEDED, _codes(limited))

    def test_scan_bytes_carries_hashes_and_combines_path_and_content_findings(self) -> None:
        raw = b"safe text\n"
        digest = _sha256(raw)
        oid = "a" * 40
        findings = policy.scan_bytes(
            "calc/POTCAR",
            raw,
            "calculation-payload",
            "active-release",
            digest,
            oid,
        )
        self.assertIn(policy.RESTRICTED_POTENTIAL_PATH, _codes(findings))
        self.assertTrue(all(item.file_sha256 == digest for item in findings))
        self.assertTrue(all(item.blob_oid == oid for item in findings))

    def test_findings_are_deterministic_unique_and_sorted(self) -> None:
        raw = (
            b"api_" + b"key=" + (b"Z9y8X7w6" * 4) + b"\n"
            b"/home/" + b"real-scientist" + b"/private/data\n"
        )
        digest = _sha256(raw)
        first = policy.scan_bytes(
            "runtime/.env",
            raw,
            "structured-record",
            "repository",
            digest,
        )
        second = policy.scan_bytes(
            "runtime/.env",
            raw,
            "structured-record",
            "repository",
            digest,
        )
        self.assertEqual(first, second)
        self.assertEqual(first, tuple(sorted(set(first))))

    def test_safe_source_has_no_findings(self) -> None:
        raw = b"def add(left: int, right: int) -> int:\n    return left + right\n"
        self.assertEqual(
            policy.scan_bytes(
                "tools/add.py",
                raw,
                "repository-source",
                "repository",
                _sha256(raw),
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
