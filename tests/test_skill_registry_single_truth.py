from __future__ import annotations

import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import install_skills  # noqa: E402
import skill_registry  # noqa: E402
import software_registry  # noqa: E402
from registry_yaml import (  # noqa: E402
    MAX_YAML_BYTES,
    RegistryYAMLError,
    load_yaml_strict,
    loads_yaml_bytes_strict,
    loads_yaml_strict,
)


ACTIVE_SKILLS = (
    "cif-structure-analysis",
    "qe-rigorous-calculations",
    "vasp-rigorous-calculations",
    "cp2k-rigorous-calculations",
    "siesta-rigorous-calculations",
    "dft-postprocess",
    "dft-campaign-efficiency",
)


class StrictYAMLTests(unittest.TestCase):
    def test_duplicate_keys_at_any_depth_and_merge_overrides_fail_closed(self) -> None:
        for text in (
            "schema_version: '1.0'\nskills: {}\nskills: {}\n",
            "root:\n  nested: 1\n  nested: 2\n",
            "base: &base\n  lifecycle: planned\nentry:\n  <<: *base\n  lifecycle: active\n",
        ):
            with self.subTest(text=text):
                with self.assertRaisesRegex(RegistryYAMLError, "YAML_DUPLICATE_KEY"):
                    loads_yaml_strict(text, "/private/secret/registry.yaml")

        secret_key = "credential_token_do_not_echo"
        with self.assertRaisesRegex(RegistryYAMLError, "YAML_DUPLICATE_KEY") as caught:
            loads_yaml_strict(f"{secret_key}: one\n{secret_key}: two\n", "registry.yaml")
        self.assertNotIn(secret_key, str(caught.exception))

    def test_unsafe_tags_and_nonmapping_roots_are_rejected_without_host_paths(self) -> None:
        with self.assertRaisesRegex(RegistryYAMLError, "YAML_UNSAFE_TAG") as unsafe:
            loads_yaml_strict("value: !!python/object/apply:os.system ['id']\n", "/private/x.yaml")
        self.assertNotIn("/private", str(unsafe.exception))
        with self.assertRaisesRegex(RegistryYAMLError, "YAML_ROOT_NOT_MAPPING"):
            loads_yaml_strict("- one\n- two\n", "registry.yaml")

    def test_anchor_aliases_are_accepted_but_validators_do_not_mutate_loaded_data(self) -> None:
        registry = skill_registry.load_registry()
        before = copy.deepcopy(registry)
        software = software_registry.load_registry()
        interfaces = load_yaml_strict(ROOT / "registry" / "interface-registry.yaml")
        environments = load_yaml_strict(ROOT / "registry" / "environment-profiles.yaml")
        skill_registry.validation_errors(
            registry,
            software_data=software,
            interface_data=interfaces,
            environment_data=environments,
        )
        self.assertEqual(registry, before)

        reused = loads_yaml_strict(
            "base: &base\n  lifecycle: planned\nentry:\n  <<: *base\n",
            "anchors.yaml",
        )
        self.assertEqual(reused["entry"], {"lifecycle": "planned"})

    def test_recursive_alias_depth_size_bom_and_encoding_limits_fail_closed(self) -> None:
        with self.assertRaisesRegex(RegistryYAMLError, "YAML_GRAPH_CYCLE"):
            loads_yaml_strict("root: &loop\n  child: *loop\n", "cycle.yaml")

        deep = "value: " + "[" * 80 + "0" + "]" * 80 + "\n"
        with self.assertRaisesRegex(RegistryYAMLError, "YAML_LIMIT_DEPTH"):
            loads_yaml_strict(deep, "deep.yaml")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversize.yaml"
            path.write_bytes(b"x" * (MAX_YAML_BYTES + 1))
            with self.assertRaisesRegex(RegistryYAMLError, "YAML_SIZE_LIMIT"):
                load_yaml_strict(path)

            path.write_bytes(b"\xef\xbb\xbfroot: {}\n")
            with self.assertRaisesRegex(RegistryYAMLError, "YAML_BOM_FORBIDDEN"):
                load_yaml_strict(path)

            path.write_bytes(b"root: \xff\n")
            with self.assertRaisesRegex(RegistryYAMLError, "YAML_ENCODING_INVALID"):
                load_yaml_strict(path)

        self.assertEqual(
            loads_yaml_bytes_strict(b"root: value\n", "bytes.yaml"),
            {"root": "value"},
        )
        with self.assertRaisesRegex(RegistryYAMLError, "YAML_SIZE_LIMIT"):
            loads_yaml_bytes_strict(b"root: value\n", "bytes.yaml", max_bytes=4)

    def test_file_loader_rejects_symlink_and_hardlink_registry_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.yaml"
            source.write_text("schema_version: '1.0'\n", encoding="utf-8")
            symlink = root / "symlink.yaml"
            symlink.symlink_to(source)
            with self.assertRaisesRegex(RegistryYAMLError, "YAML_UNREADABLE"):
                load_yaml_strict(symlink)

            hardlink = root / "hardlink.yaml"
            os.link(source, hardlink)
            with self.assertRaisesRegex(RegistryYAMLError, "YAML_HARDLINK_FORBIDDEN"):
                load_yaml_strict(hardlink)


class SkillRegistrySingleTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skills = skill_registry.load_registry()
        cls.software = software_registry.load_registry()
        cls.interfaces = load_yaml_strict(ROOT / "registry" / "interface-registry.yaml")
        cls.environments = load_yaml_strict(ROOT / "registry" / "environment-profiles.yaml")

    def semantic_errors(self, skills=None, software=None, environments=None):
        return skill_registry.validation_errors(
            skills or self.skills,
            software_data=software or self.software,
            interface_data=self.interfaces,
            environment_data=environments or self.environments,
        )

    def test_active_set_and_paths_have_one_canonical_source(self) -> None:
        self.assertEqual(skill_registry.active_skill_names(), ACTIVE_SKILLS)
        active = {
            name: entry
            for name, entry in self.skills["skills"].items()
            if entry["lifecycle"] == "active"
        }
        self.assertEqual(tuple(active), ACTIVE_SKILLS)
        for name, entry in active.items():
            self.assertEqual(entry["path"], f"skills/{name}")
            self.assertRegex(entry["source_tree_sha256"], r"^[a-f0-9]{64}$")
            self.assertNotIn("side_effect_class", entry)

    def test_semantic_snapshot_is_valid_before_source_hygiene_gate(self) -> None:
        self.assertEqual(self.semantic_errors(), [])
        self.assertEqual(software_registry.validation_errors(self.software, ROOT), [])

    def test_interfaces_resolve_and_active_skills_cannot_use_planned_contracts(self) -> None:
        unknown = copy.deepcopy(self.skills)
        unknown["skills"]["qe-rigorous-calculations"]["produces"].append("invented-proof@1.0")
        failures = self.semantic_errors(unknown)
        self.assertTrue(any("unknown interface" in item for item in failures))

        planned = copy.deepcopy(self.skills)
        planned["skills"]["qe-rigorous-calculations"]["produces"].append("ovito-pipeline-spec@1.0")
        failures = self.semantic_errors(planned)
        self.assertTrue(any("active skill cannot use non-active interface" in item for item in failures))

    def test_legacy_side_effect_and_noncanonical_effect_sets_are_rejected(self) -> None:
        legacy = copy.deepcopy(self.skills)
        entry = legacy["skills"]["qe-rigorous-calculations"]
        entry["side_effect_class"] = "local-write"
        del entry["side_effects"]
        self.assertTrue(any("expected fields" in item for item in self.semantic_errors(legacy)))

        empty = copy.deepcopy(self.skills)
        empty["skills"]["qe-rigorous-calculations"]["side_effects"] = []
        self.assertTrue(any("expected a nonempty list" in item for item in self.semantic_errors(empty)))

        reordered = copy.deepcopy(self.skills)
        reordered["skills"]["qe-rigorous-calculations"]["side_effects"] = [
            "local-execution",
            "network-read",
            "local-write",
        ]
        self.assertTrue(any("canonical order" in item for item in self.semantic_errors(reordered)))

    def test_planned_activation_is_structured_and_exactly_cross_registered(self) -> None:
        prose = copy.deepcopy(self.skills)
        prose["skills"]["gaussian-rigorous-calculations"]["activation_requirements"] = ["x"]
        self.assertTrue(any("structured mapping" in item for item in self.semantic_errors(prose)))

        wrong_check = copy.deepcopy(self.skills)
        requirements = wrong_check["skills"]["gaussian-rigorous-calculations"]["activation_requirements"]
        requirements["activation_check_ids"][-1] = "made-up-check"
        self.assertTrue(any("13 fixed checks" in item for item in self.semantic_errors(wrong_check)))

        borrowed_profile = copy.deepcopy(self.skills)
        profile = borrowed_profile["skills"]["gaussian-rigorous-calculations"]["activation_requirements"][
            "software_profiles"
        ][0]
        profile["environment_profile_ids"] = ["rdkit-pypi"]
        self.assertTrue(any("planned software/provider mappings" in item for item in self.semantic_errors(borrowed_profile)))

    def test_software_role_profile_integration_and_reverse_ownership_are_closed(self) -> None:
        wrong_role_profile = copy.deepcopy(self.software)
        wrong_role_profile["planned_software"]["gaussian"]["activation_profile"] = "structure-library"
        self.assertTrue(
            any("must equal provider role" in item for item in software_registry.validation_errors(wrong_role_profile))
        )
        wrong_integration = copy.deepcopy(self.software)
        wrong_integration["planned_software"]["gaussian"]["intended_integration"] = "structure-adapter"
        self.assertTrue(
            any("requires 'calculation-skill'" in item for item in software_registry.validation_errors(wrong_integration))
        )
        duplicate_owner = copy.deepcopy(self.software)
        duplicate_owner["planned_software"]["gaussian"]["environment_profiles"]["profile_ids"] = [
            "gromacs-cpu"
        ]
        failures = software_registry.validation_errors(duplicate_owner, environment_data=self.environments)
        self.assertTrue(any("already owned" in item for item in failures))
        self.assertTrue(any("unowned" in item for item in failures))

    def test_unknown_intended_skill_is_rejected_but_staged_provider_does_not_define_lifecycle(self) -> None:
        unknown = copy.deepcopy(self.software)
        unknown["planned_software"]["gaussian"]["intended_skill"] = "missing-skill"
        failures = self.semantic_errors(software=unknown)
        self.assertTrue(any("missing skill placeholder" in item for item in failures))

        staged = copy.deepcopy(self.skills)
        staged_entry = staged["skills"]["ml-potential-workflows"]
        staged_entry["lifecycle"] = "active"
        staged_entry["path"] = "skills/ml-potential-workflows"
        staged_entry["source_tree_sha256"] = "0" * 64
        staged_entry["activation_requirements"] = {
            "software_profiles": [],
            "interface_ids": [],
            "activation_check_ids": [],
            "task_catalog_ids": [],
        }
        failures = self.semantic_errors(staged)
        self.assertFalse(any("must remain planned" in item for item in failures))

    def test_software_mutation_cannot_change_installer_active_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "registry").mkdir()
            fixture = copy.deepcopy(self.skills)
            for name, entry in fixture["skills"].items():
                if entry["lifecycle"] != "active":
                    continue
                source = root / "skills" / name
                source.mkdir(parents=True)
                source.joinpath("SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
                entry["source_tree_sha256"] = skill_registry.source_tree_digest(source).sha256
            (root / "registry" / "skill-registry.yaml").write_text(
                yaml.safe_dump(fixture, sort_keys=False), encoding="utf-8"
            )
            (root / "registry" / "software-registry.yaml").write_text(
                "schema_version: '1.0'\nsoftware:\n  qe:\n    lifecycle: deprecated\n    calculation_skill: attacker\n",
                encoding="utf-8",
            )
            self.assertEqual(install_skills.installable_skill_names(root), ACTIVE_SKILLS)

    def test_selected_install_validates_its_own_tree_without_hiding_other_tree_damage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("registry").mkdir()
            fixture = copy.deepcopy(self.skills)
            for name, entry in fixture["skills"].items():
                if entry["lifecycle"] != "active":
                    continue
                source = root / "skills" / name
                source.mkdir(parents=True)
                source.joinpath("SKILL.md").write_text(
                    f"---\nname: {name}\n---\n", encoding="utf-8"
                )
            damaged = root / "skills" / "qe-rigorous-calculations"
            damaged.joinpath("reference 2.md").write_text("duplicate", encoding="utf-8")
            for name, entry in fixture["skills"].items():
                if entry["lifecycle"] == "active":
                    entry["source_tree_sha256"] = skill_registry.source_tree_digest(
                        root / "skills" / name
                    ).sha256
            root.joinpath("registry", "skill-registry.yaml").write_text(
                yaml.safe_dump(fixture, sort_keys=False), encoding="utf-8"
            )

            self.assertEqual(
                skill_registry.validate_selected_active_sources(
                    ("cif-structure-analysis",), root
                ),
                ("cif-structure-analysis",),
            )
            with self.assertRaisesRegex(ValueError, "copy-like source path"):
                skill_registry.validate_selected_active_sources(
                    ("qe-rigorous-calculations",), root
                )
            with self.assertRaisesRegex(ValueError, "copy-like source path"):
                skill_registry.validate_active_sources(root)

    def test_actual_source_hashes_are_fresh_and_copy_artifact_free(self) -> None:
        failures = skill_registry.validation_errors(self.skills, ROOT)
        self.assertFalse(any("copy-like source path" in item for item in failures))
        self.assertFalse(any("recorded" in item and "!= actual" in item for item in failures))


class SourceTreeDigestTests(unittest.TestCase):
    def test_hash_binds_relative_paths_and_raw_bytes_without_absolute_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("a.txt").write_bytes(b"same")
            first = skill_registry.source_tree_digest(root)
            root.joinpath("a.txt").rename(root / "b.txt")
            second = skill_registry.source_tree_digest(root)
            self.assertNotEqual(first.sha256, second.sha256)
            self.assertEqual(second.files[0].path, "b.txt")
            self.assertNotIn(str(root), second.files[0].path)

    def test_symlink_special_and_hardlink_entries_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("source.txt").write_text("x", encoding="utf-8")
            root.joinpath("alias.txt").symlink_to(root / "source.txt")
            with self.assertRaisesRegex(ValueError, "symlink"):
                skill_registry.source_tree_digest(root)
            root.joinpath("alias.txt").unlink()
            os.link(root / "source.txt", root / "hard.txt")
            with self.assertRaisesRegex(ValueError, "hard-linked"):
                skill_registry.source_tree_digest(root)


if __name__ == "__main__":
    unittest.main()
