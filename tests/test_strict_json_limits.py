from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import strict_json  # noqa: E402


class StrictJSONLimitTests(unittest.TestCase):
    def assert_limit(self, raw: bytes, message: str, **limits: int) -> None:
        with self.assertRaisesRegex(strict_json.StrictJSONError, message):
            strict_json.loads_value(raw, "fixture.json", **limits)

    def test_byte_limit_is_checked_before_decode(self) -> None:
        self.assert_limit(b'{"value":"1234"}', "maximum JSON byte length", max_bytes=4)

    def test_depth_limit_is_preflighted_without_traceback(self) -> None:
        raw = b"[" * 32 + b"0" + b"]" * 32
        self.assert_limit(raw, "maximum JSON nesting depth", max_depth=8)

    def test_wide_document_has_explicit_node_limit(self) -> None:
        raw = ("[" + ",".join("0" for _ in range(32)) + "]").encode("ascii")
        self.assert_limit(raw, "maximum JSON node count", max_nodes=16)

    def test_string_and_number_tokens_have_explicit_limits(self) -> None:
        self.assert_limit(b'"123456789"', "maximum JSON string length", max_string_chars=8)
        self.assert_limit(b"123456789", "maximum JSON number length", max_number_chars=8)

    def test_float_overflow_is_rejected_as_nonfinite(self) -> None:
        self.assert_limit(b"1e999", "non-finite JSON number")

    def test_root_wrappers_preserve_api_and_forward_limits(self) -> None:
        self.assertEqual(strict_json.loads_object(b'{"x":1}', "object.json"), {"x": 1})
        self.assertEqual(strict_json.loads_array(b"[1]", "array.json"), [1])
        with self.assertRaisesRegex(strict_json.StrictJSONError, "node count"):
            strict_json.loads_array(b"[1,2]", max_nodes=2)

    def test_invalid_limits_are_programmer_errors(self) -> None:
        with self.assertRaises(ValueError):
            strict_json.loads_value(b"null", max_bytes=0)

    def test_path_loader_bounds_before_full_read_and_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "input.json"
            path.write_bytes(b'{"value":"123456789"}')
            with self.assertRaisesRegex(strict_json.StrictJSONError, "byte length"):
                strict_json.load_object(path, max_bytes=8)
            self.assertEqual(strict_json.load_object(path)["value"], "123456789")
            alias = root / "alias.json"
            alias.symlink_to(path.name)
            with self.assertRaisesRegex(strict_json.StrictJSONError, "unsafe"):
                strict_json.load_object(alias)


if __name__ == "__main__":
    unittest.main(verbosity=2)
