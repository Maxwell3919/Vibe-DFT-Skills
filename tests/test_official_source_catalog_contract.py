from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


class OfficialSourceCatalogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema = json.loads(
            (
                ROOT
                / "contracts"
                / "official-document-source-catalog-1.1.schema.json"
            ).read_text(encoding="utf-8")
        )
        cls.validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

    @staticmethod
    def catalogs() -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        for path in sorted(ROOT.glob("skills/*/references/**/*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            if (
                isinstance(value, dict)
                and value.get("contract_name")
                == "official-document-source-catalog"
            ):
                result.append((path, value))
        return result

    def test_every_live_source_id_is_already_output_safe(self) -> None:
        catalogs = self.catalogs()
        self.assertEqual(len(catalogs), 55)
        dispositions: set[str] = set()
        for path, catalog in catalogs:
            errors = list(self.validator.iter_errors(catalog))
            with self.subTest(path=path):
                self.assertEqual([error.message for error in errors], [])
            sources = catalog["discovered_sources"]
            self.assertIsInstance(sources, dict)
            dispositions.update(
                source["disposition"] for source in sources.values()
            )
        self.assertEqual(dispositions, {"included", "excluded"})

    def test_unsafe_source_id_fails_at_the_input_boundary(self) -> None:
        _path, catalog = self.catalogs()[0]
        mutation = copy.deepcopy(catalog)
        sources = mutation["discovered_sources"]
        source_id = next(iter(sources))
        sources["Unsafe:Source:ID"] = sources.pop(source_id)
        errors = list(self.validator.iter_errors(mutation))
        self.assertTrue(
            any(
                list(error.absolute_path) == ["discovered_sources"]
                and error.validator == "pattern"
                for error in errors
            )
        )


if __name__ == "__main__":
    unittest.main()
