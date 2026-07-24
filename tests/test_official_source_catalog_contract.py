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
                / "official-document-source-catalog.schema.json"
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
        self.assertGreater(len(catalogs), 0)
        for path, catalog in catalogs:
            errors = list(self.validator.iter_errors(catalog))
            with self.subTest(path=path):
                self.assertEqual([error.message for error in errors], [])

    def test_unsafe_source_id_fails_at_the_input_boundary(self) -> None:
        _path, catalog = self.catalogs()[0]
        mutation = copy.deepcopy(catalog)
        mutation["sources"][0]["source_id"] = "Unsafe:Source:ID"
        errors = list(self.validator.iter_errors(mutation))
        self.assertTrue(
            any(
                list(error.absolute_path)[-1:] == ["source_id"]
                for error in errors
            )
        )


if __name__ == "__main__":
    unittest.main()
