from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from . import __version__


FINGERPRINT_ALGORITHM = "sha256-ordered-cell-sites-v1"
FINGERPRINT_CANONICALIZATION = "json-sort-keys-compact-utf8-v1"
FINGERPRINT_DECIMAL_PLACES = 10


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ordered_structure_fingerprint_input(atoms: Any) -> dict[str, Any]:
    """Return the exact JSON-shaped preimage used by the v1 fingerprint."""

    return {
        "cell_vectors_ang": [
            [round(float(value), FINGERPRINT_DECIMAL_PLACES) for value in row]
            for row in atoms.cell.array
        ],
        "pbc": [bool(value) for value in atoms.get_pbc()],
        "sites": [
            {
                "atomic_number": int(number),
                "fractional": [
                    round(
                        float(value) % 1.0,
                        FINGERPRINT_DECIMAL_PLACES,
                    )
                    for value in position
                ],
            }
            for number, position in zip(
                atoms.get_atomic_numbers(), atoms.get_scaled_positions(wrap=True)
            )
        ],
    }


def fingerprint_value(fingerprint_input: dict[str, Any]) -> str:
    """Hash the v1 preimage with the frozen compact sorted-key JSON rule."""

    canonical = json.dumps(
        fingerprint_input,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def ordered_structure_fingerprint(atoms: Any) -> dict[str, Any]:
    payload = ordered_structure_fingerprint_input(atoms)
    return {
        "algorithm": FINGERPRINT_ALGORITHM,
        "value": fingerprint_value(payload),
        "canonicalization": FINGERPRINT_CANONICALIZATION,
        "fingerprint_input": payload,
        "equivalence_scope": (
            "same ordered atomic numbers, cell vectors, PBC, and wrapped fractional "
            "coordinates after rounding to 10 decimal places and compact sorted-key "
            "UTF-8 JSON canonicalization; not invariant to origin, basis, symmetry, "
            "or supercell"
        ),
    }


def element_styles(atoms: Any) -> dict[str, dict[str, Any]]:
    from ase.data import atomic_numbers, covalent_radii
    from ase.data.colors import jmol_colors

    styles = {}
    for symbol in sorted(set(atoms.get_chemical_symbols())):
        number = atomic_numbers[symbol]
        rgb = jmol_colors[number]
        color = "#" + "".join(f"{max(0, min(255, round(float(value) * 255))):02X}" for value in rgb)
        radius = float(covalent_radii[number])
        if not math.isfinite(radius) or radius <= 0:
            radius = 1.2
        styles[symbol] = {
            "atomic_number": number,
            "color_hex": color,
            "covalent_radius_ang": round(radius, 6),
            "display_radius_ang": round(max(0.16, min(0.42, radius * 0.2)), 6),
            "style_source": "ASE Jmol colors and covalent radii",
        }
    return styles


def relative_artifact_path(path: Path, artifact_root: Path) -> str:
    return Path(os.path.relpath(path, start=artifact_root)).as_posix()


def validation_from_diagnostics(
    diagnostics: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized = []
    for item in diagnostics:
        status = str(item.get("status", "warn")).lower()
        if status not in {"pass", "warn", "fail", "not-run"}:
            status = "warn"
        normalized.append(
            {
                "id": str(item.get("id", "unspecified-diagnostic")),
                "status": status,
                "message": str(item.get("message", "")),
            }
        )
    if any(item["status"] == "fail" for item in normalized):
        overall = "block"
    elif any(item["status"] == "warn" for item in normalized):
        overall = "warn"
    else:
        overall = "pass"
    return {"status": overall, "checks": normalized}


def manifest_identity(document: dict[str, Any], atoms: Any, source_label: str) -> dict[str, Any]:
    selected = document["selected_block"]
    source_hash = document["sha256"]
    manifest_id = f"structure-{source_hash[:16]}-b{selected['index']}"
    return {
        "schema_version": "1.0",
        "manifest_id": manifest_id,
        "source": {
            "role": "source-cif",
            "label": source_label,
            "format": document["syntax"],
            "sha256": source_hash,
            "bytes": document["bytes"],
            "data_block": selected,
        },
        "parser": document["parser"],
        "structure_identity": ordered_structure_fingerprint(atoms),
        "transformations": [],
    }


def provenance(command_options: dict[str, Any], dependency_versions: dict[str, str]) -> dict[str, Any]:
    return {
        "producer": "cif-structure-analysis",
        "producer_version": __version__,
        "generated_utc": utc_now(),
        "command": ["analyze_cif.py", "--input", "<input-cif>", "--json", "<analysis-json>", "--markdown", "<analysis-markdown>"],
        "command_options": command_options,
        "dependency_versions": dependency_versions,
    }


def schema_errors(manifest: dict[str, Any], script_path: Path) -> list[str]:
    from jsonschema import Draft202012Validator, FormatChecker

    root = script_path.resolve().parents[3]
    schema_path = root / "contracts" / "structure-manifest.schema.json"
    if not schema_path.is_file():
        return [f"structure manifest schema is unavailable: {schema_path}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = []
    for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        failures.append(f"{location}: {error.message}")
    return failures
