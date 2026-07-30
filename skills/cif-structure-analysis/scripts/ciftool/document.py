from __future__ import annotations

import hashlib
import importlib.metadata
import math
from pathlib import Path
import re
from collections import Counter
from typing import Any, Callable, Iterable


_CIF_NUMBER = re.compile(
    r"^([+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[Ee][+-]?\d+)?)(?:\((\d+)\))?$"
)


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_cif_syntax(path: Path) -> str:
    with path.open("rb") as handle:
        first = handle.readline(4096)
    if first.startswith(b"\xef\xbb\xbf"):
        first = first[3:]
    return "cif2.0" if first.rstrip(b"\r\n") == b"#\\#CIF_2.0" else "cif1.1"


def _clean_cif_string(value: Any) -> str:
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def parse_cif_number(value: Any) -> dict[str, Any]:
    raw = str(value).strip()
    clean = _clean_cif_string(raw)
    if clean in {"", ".", "?"}:
        return {"raw": raw, "value": None, "standard_uncertainty": None}
    match = _CIF_NUMBER.fullmatch(clean)
    if not match:
        return {"raw": raw, "value": None, "standard_uncertainty": None}
    number_text, su_digits = match.groups()
    number = float(number_text)
    standard_uncertainty = None
    if su_digits is not None:
        mantissa, _, exponent_text = number_text.upper().partition("E")
        decimals = len(mantissa.partition(".")[2]) if "." in mantissa else 0
        exponent = int(exponent_text) if exponent_text else 0
        standard_uncertainty = int(su_digits) * 10.0 ** (exponent - decimals)
    return {
        "raw": raw,
        "value": number if math.isfinite(number) else None,
        "standard_uncertainty": standard_uncertainty,
    }


def _string_record(tag: str | None, values: list[str]) -> dict[str, Any]:
    raw = values[0] if values else None
    return {
        "tag": tag,
        "raw": raw,
        "value": _clean_cif_string(raw) if raw is not None else None,
    }


def _numeric_record(tag: str | None, values: list[str]) -> dict[str, Any]:
    parsed = parse_cif_number(values[0]) if values else {
        "raw": None,
        "value": None,
        "standard_uncertainty": None,
    }
    return {"tag": tag, **parsed}


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    try:
        return [str(item) for item in value]
    except TypeError:
        return [str(value)]


def _metadata_from_getter(
    get_values: Callable[[Iterable[str]], tuple[str | None, list[str]]]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    cell_aliases = {
        "a": ("_cell_length_a", "_cell.length_a"),
        "b": ("_cell_length_b", "_cell.length_b"),
        "c": ("_cell_length_c", "_cell.length_c"),
        "alpha": ("_cell_angle_alpha", "_cell.angle_alpha"),
        "beta": ("_cell_angle_beta", "_cell.angle_beta"),
        "gamma": ("_cell_angle_gamma", "_cell.angle_gamma"),
    }
    cell: dict[str, Any] = {}
    for name, aliases in cell_aliases.items():
        tag, values = get_values(aliases)
        cell[name] = _numeric_record(tag, values)

    hm_tag, hm_values = get_values(
        (
            "_space_group_name_H-M_alt",
            "_symmetry_space_group_name_H-M",
            "_space_group.name_H-M_alt",
        )
    )
    number_tag, number_values = get_values(
        (
            "_space_group_IT_number",
            "_symmetry_Int_Tables_number",
            "_space_group.IT_number",
        )
    )
    hall_tag, hall_values = get_values(
        ("_space_group_name_Hall", "_symmetry_space_group_name_Hall", "_space_group.name_Hall")
    )

    formula_sum_tag, formula_sum_values = get_values(
        ("_chemical_formula_sum", "_chemical_formula.sum")
    )
    formula_struct_tag, formula_struct_values = get_values(
        ("_chemical_formula_structural", "_chemical_formula.structural")
    )
    z_tag, z_values = get_values(("_cell_formula_units_Z", "_cell.Z_PDB"))

    site_aliases = {
        "label": ("_atom_site_label", "_atom_site.label"),
        "type_symbol": ("_atom_site_type_symbol", "_atom_site.type_symbol"),
        "fract_x": ("_atom_site_fract_x", "_atom_site.fract_x"),
        "fract_y": ("_atom_site_fract_y", "_atom_site.fract_y"),
        "fract_z": ("_atom_site_fract_z", "_atom_site.fract_z"),
        "cartn_x": ("_atom_site_Cartn_x", "_atom_site.Cartn_x"),
        "cartn_y": ("_atom_site_Cartn_y", "_atom_site.Cartn_y"),
        "cartn_z": ("_atom_site_Cartn_z", "_atom_site.Cartn_z"),
        "occupancy": ("_atom_site_occupancy", "_atom_site.occupancy"),
        "wyckoff_symbol": ("_atom_site_Wyckoff_symbol", "_atom_site.Wyckoff_symbol"),
        "site_symmetry_multiplicity": (
            "_atom_site_site_symmetry_multiplicity",
            "_atom_site.site_symmetry_multiplicity",
            "_atom_site_symmetry_multiplicity",
            "_atom_site.symmetry_multiplicity",
        ),
        "site_symmetry_order": (
            "_atom_site_site_symmetry_order",
            "_atom_site.site_symmetry_order",
        ),
        "disorder_assembly": ("_atom_site_disorder_assembly", "_atom_site.disorder_assembly"),
        "disorder_group": ("_atom_site_disorder_group", "_atom_site.disorder_group"),
        "adp_type": ("_atom_site_adp_type", "_atom_site.adp_type"),
        "calc_flag": ("_atom_site_calc_flag", "_atom_site.calc_flag"),
        "u_iso": ("_atom_site_U_iso_or_equiv", "_atom_site.U_iso_or_equiv"),
        "b_iso": ("_atom_site_B_iso_or_equiv", "_atom_site.B_iso_or_equiv"),
    }
    site_columns: dict[str, tuple[str | None, list[str]]] = {
        name: get_values(aliases) for name, aliases in site_aliases.items()
    }
    site_count = max((len(values) for _, values in site_columns.values()), default=0)
    atom_sites = []
    diagnostics: list[dict[str, str]] = []
    for index in range(site_count):
        row: dict[str, Any] = {"row": index}
        for name, (tag, values) in site_columns.items():
            raw = values[index] if index < len(values) else None
            if name in {
                "fract_x",
                "fract_y",
                "fract_z",
                "cartn_x",
                "cartn_y",
                "cartn_z",
                "occupancy",
                "site_symmetry_multiplicity",
                "site_symmetry_order",
                "u_iso",
                "b_iso",
            }:
                row[name] = {"tag": tag, **parse_cif_number(raw)} if raw is not None else {
                    "tag": tag,
                    "raw": None,
                    "value": None,
                    "standard_uncertainty": None,
                }
            else:
                row[name] = {
                    "tag": tag,
                    "raw": raw,
                    "value": _clean_cif_string(raw) if raw is not None else None,
                }
        atom_sites.append(row)
        fractional_complete = all(
            row[axis]["value"] is not None for axis in ("fract_x", "fract_y", "fract_z")
        )
        cartesian_complete = all(
            row[axis]["value"] is not None for axis in ("cartn_x", "cartn_y", "cartn_z")
        )
        if not fractional_complete and not cartesian_complete:
            diagnostics.append(
                {
                    "id": "atom-site-coordinate-incomplete",
                    "status": "warn",
                    "message": (
                        f"atom-site row {index} lacks a complete numeric fractional or Cartesian coordinate"
                    ),
                }
            )
        occupancy = row["occupancy"]["value"]
        if occupancy is not None and (occupancy < 0 or occupancy > 1):
            diagnostics.append(
                {
                    "id": "atom-site-occupancy-range",
                    "status": "fail",
                    "message": f"atom-site row {index} has occupancy {occupancy} outside [0, 1]",
                }
            )

    partial_occupancy_rows = [
        row["row"]
        for row in atom_sites
        if row["occupancy"]["value"] is not None
        and not math.isclose(float(row["occupancy"]["value"]), 1.0, abs_tol=1e-8)
    ]
    if partial_occupancy_rows:
        diagnostics.append(
            {
                "id": "partial-occupancy-present",
                "status": "warn",
                "message": f"partial occupancy is present in atom-site rows {partial_occupancy_rows}",
            }
        )

    disorder_rows = [
        row["row"]
        for row in atom_sites
        if row["disorder_assembly"]["value"] not in {None, ".", "?"}
        or row["disorder_group"]["value"] not in {None, ".", "?"}
    ]
    if disorder_rows:
        diagnostics.append(
            {
                "id": "atom-site-disorder-metadata-present",
                "status": "warn",
                "message": (
                    f"positional disorder metadata is present in atom-site rows {disorder_rows}; "
                    "the ASE structure adapter does not resolve correlated disorder assemblies"
                ),
            }
        )

    labels = [row["label"]["value"] for row in atom_sites if row["label"]["value"]]
    duplicate_labels = sorted(label for label, count in Counter(labels).items() if count > 1)
    if duplicate_labels:
        diagnostics.append(
            {
                "id": "atom-site-label-duplicate",
                "status": "warn",
                "message": f"duplicate atom-site labels are present: {duplicate_labels}",
            }
        )

    symop_tag, symop_values = get_values(
        (
            "_space_group_symop_operation_xyz",
            "_symmetry_equiv_pos_as_xyz",
            "_space_group_symop.operation_xyz",
        )
    )
    audit = {}
    for key, aliases in {
        "creation_method": ("_audit_creation_method", "_audit.creation_method"),
        "creation_date": ("_audit_creation_date", "_audit.creation_date"),
        "database_code_cod": ("_cod_database_code", "_database_code_COD"),
        "doi": ("_journal_paper_doi", "_citation_DOI", "_citation.DOI"),
    }.items():
        tag, values = get_values(aliases)
        audit[key] = _string_record(tag, values)

    return (
        {
            "cell": cell,
            "declared_formula": {
                "sum": _string_record(formula_sum_tag, formula_sum_values),
                "structural": _string_record(formula_struct_tag, formula_struct_values),
                "formula_units_z": _numeric_record(z_tag, z_values),
            },
            "declared_symmetry": {
                "hermann_mauguin": _string_record(hm_tag, hm_values),
                "international_tables_number": _numeric_record(number_tag, number_values),
                "hall": _string_record(hall_tag, hall_values),
                "operation_tag": symop_tag,
                "operation_count": len(symop_values),
                "operations": [_clean_cif_string(item) for item in symop_values],
            },
            "atom_site_count": site_count,
            "atom_sites": atom_sites,
            "partial_occupancy_rows": partial_occupancy_rows,
            "disorder_rows": disorder_rows,
            "audit": audit,
        },
        diagnostics,
    )


def _select_block(
    names: list[str], block_name: str | None, block_index: int | None
) -> tuple[int, str]:
    if not names:
        raise RuntimeError("failed to read CIF: document contains no data blocks")
    if block_name is not None:
        matches = [index for index, name in enumerate(names) if name.casefold() == block_name.casefold()]
        if not matches:
            raise RuntimeError(
                f"failed to select CIF data block {block_name!r}; available blocks: {', '.join(names)}"
            )
        if len(matches) > 1:
            raise RuntimeError(
                f"failed to select CIF data block {block_name!r}; "
                "the case-insensitive name is ambiguous"
            )
        return matches[0], names[matches[0]]
    selected = 0 if block_index is None else block_index
    if selected < 0 or selected >= len(names):
        raise RuntimeError(
            f"failed to select CIF data block index {selected}; valid range is 0..{len(names) - 1}"
        )
    return selected, names[selected]


def materialize_selected_block(
    path: Path,
    selected_block: dict[str, Any],
    document_blocks: list[dict[str, Any]],
) -> Any:
    """Materialize the exact raw CIF block instead of an image-list ordinal.

    ``ase.io.read(index=N)`` indexes only blocks that ASE can materialize.
    Raw document ordinals also include metadata-only blocks, so the two index
    spaces are not interchangeable.
    """

    from ase.io.cif import parse_cif

    try:
        with path.open(encoding="utf-8-sig") as handle:
            ase_blocks = list(parse_cif(handle))
    except Exception as exc:
        raise RuntimeError(f"failed to parse CIF blocks with the ASE structure adapter: {exc}") from exc

    expected_names = [str(item["name"]) for item in document_blocks]
    observed_names = [str(block.name) for block in ase_blocks]
    if len(expected_names) != len(observed_names) or any(
        expected.casefold() != observed.casefold()
        for expected, observed in zip(expected_names, observed_names)
    ):
        raise RuntimeError(
            "failed to bind the selected CIF data block: raw-parser and "
            "structure-adapter block inventories disagree"
        )

    index = int(selected_block["index"])
    if index < 0 or index >= len(ase_blocks):
        raise RuntimeError("failed to bind the selected CIF data block by raw ordinal")
    observed_name = observed_names[index]
    if observed_name.casefold() != str(selected_block["name"]).casefold():
        raise RuntimeError(
            "failed to bind the selected CIF data block: selected names disagree"
        )
    try:
        atoms = ase_blocks[index].get_atoms(
            store_tags=True,
            fractional_occupancies=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"selected CIF data block {selected_block['name']!r} at raw index "
            f"{index} could not be materialized as a periodic structure: {exc}"
        ) from exc
    if len(atoms) == 0:
        raise RuntimeError(
            f"selected CIF data block {selected_block['name']!r} at raw index "
            f"{index} contains no materialized sites"
        )
    return atoms


def _inspect_with_gemmi(
    path: Path, block_name: str | None, block_index: int | None
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    import gemmi

    try:
        document = gemmi.cif.read_file(str(path), check_level=2)
    except Exception as exc:
        raise RuntimeError(f"failed strict CIF 1.1 parse with Gemmi: {exc}") from exc

    blocks = []
    for index, block in enumerate(document):
        tags: list[str] = []
        pair_count = 0
        loop_count = 0
        for item in block:
            if item.pair is not None:
                pair_count += 1
                tags.append(str(item.pair[0]))
            elif item.loop is not None:
                loop_count += 1
                tags.extend(str(tag) for tag in item.loop.tags)
        blocks.append(
            {
                "index": index,
                "name": block.name,
                "tag_count": len(tags),
                "pair_count": pair_count,
                "loop_count": loop_count,
                "tags": tags,
            }
        )
    selected_index, selected_name = _select_block(
        [item["name"] for item in blocks], block_name, block_index
    )
    selected_block = document[selected_index]

    def get_values(aliases: Iterable[str]) -> tuple[str | None, list[str]]:
        for alias in aliases:
            values = selected_block.find_values(alias)
            if values:
                return alias, [str(item) for item in values]
        return None, []

    metadata, diagnostics = _metadata_from_getter(get_values)
    return (
        {
            "parser": {
                "name": "gemmi",
                "version": gemmi.__version__,
                "mode": "strict-cif1.1",
                "status": "used",
            },
            "blocks": blocks,
            "selected_block": {"index": selected_index, "name": selected_name},
            "metadata": metadata,
        },
        diagnostics,
    )


def _inspect_with_pycifrw(
    path: Path, block_name: str | None, block_index: int | None
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    try:
        from CifFile import ReadCif
    except ImportError as exc:
        raise RuntimeError("failed CIF2 parse: PyCifRW is not installed") from exc
    try:
        document = ReadCif(str(path), grammar="2.0")
    except Exception as exc:
        raise RuntimeError(f"failed strict CIF2 parse with PyCifRW: {exc}") from exc
    names = [str(name) for name in document.keys()]
    selected_index, selected_name = _select_block(names, block_name, block_index)
    selected_block = document[selected_name]
    blocks = []
    for index, name in enumerate(names):
        block = document[name]
        tags = [str(tag) for tag in block.keys()]
        loops = [list(loop) for loop in block.loops.values()]
        loop_names = {str(tag) for loop in loops for tag in loop}
        blocks.append(
            {
                "index": index,
                "name": name,
                "tag_count": len(tags),
                "pair_count": len([tag for tag in tags if tag not in loop_names]),
                "loop_count": len(loops),
                "tags": tags,
            }
        )
    tag_lookup = {str(tag).casefold(): str(tag) for tag in selected_block.keys()}

    def get_values(aliases: Iterable[str]) -> tuple[str | None, list[str]]:
        for alias in aliases:
            actual = tag_lookup.get(alias.casefold())
            if actual is not None:
                return actual, _as_string_list(selected_block[actual])
        return None, []

    metadata, diagnostics = _metadata_from_getter(get_values)
    return (
        {
            "parser": {
                "name": "PyCifRW",
                "version": _package_version("PyCifRW"),
                "mode": "strict-cif2.0",
                "status": "used",
            },
            "blocks": blocks,
            "selected_block": {"index": selected_index, "name": selected_name},
            "metadata": metadata,
        },
        diagnostics,
    )


def _inspect_with_ase_fallback(
    path: Path, block_name: str | None, block_index: int | None
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    from ase.io.cif import parse_cif

    try:
        with path.open(encoding="utf-8") as handle:
            document = list(parse_cif(handle))
    except Exception as exc:
        raise RuntimeError(f"failed fallback CIF parse with ASE: {exc}") from exc
    names = [str(block.name) for block in document]
    selected_index, selected_name = _select_block(names, block_name, block_index)
    blocks = []
    for index, block in enumerate(document):
        tags = list(block)
        blocks.append(
            {
                "index": index,
                "name": block.name,
                "tag_count": len(tags),
                "pair_count": None,
                "loop_count": None,
                "tags": tags,
            }
        )
    selected_block = document[selected_index]
    tag_lookup = {str(tag).casefold(): str(tag) for tag in selected_block}

    def get_values(aliases: Iterable[str]) -> tuple[str | None, list[str]]:
        for alias in aliases:
            actual = tag_lookup.get(alias.casefold())
            if actual is not None:
                return actual, _as_string_list(selected_block[actual])
        return None, []

    metadata, diagnostics = _metadata_from_getter(get_values)
    diagnostics.insert(
        0,
        {
            "id": "raw-parser-degraded",
            "status": "warn",
            "message": "Gemmi is unavailable; ASE fallback does not preserve raw uncertainty text",
        },
    )
    return (
        {
            "parser": {
                "name": "ase.io.cif",
                "version": _package_version("ase"),
                "mode": "degraded-cif1.1",
                "status": "degraded",
            },
            "blocks": blocks,
            "selected_block": {"index": selected_index, "name": selected_name},
            "metadata": metadata,
        },
        diagnostics,
    )


def inspect_cif_document(
    path: Path,
    block_name: str | None = None,
    block_index: int | None = 0,
) -> dict[str, Any]:
    syntax = detect_cif_syntax(path)
    if syntax == "cif2.0":
        details, diagnostics = _inspect_with_pycifrw(path, block_name, block_index)
    else:
        try:
            details, diagnostics = _inspect_with_gemmi(path, block_name, block_index)
        except ImportError:
            details, diagnostics = _inspect_with_ase_fallback(path, block_name, block_index)
    return {
        "syntax": syntax,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        **details,
        "diagnostics": diagnostics,
    }
