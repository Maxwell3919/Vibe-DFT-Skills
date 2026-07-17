from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import sha256_file, utc_now


ROLES = {
    "INCAR": "vasp-input",
    "POSCAR": "vasp-structure",
    "KPOINTS": "vasp-sampling",
    "POTCAR": "vasp-licensed-potential",
    "OUTCAR": "vasp-main-output",
    "OSZICAR": "vasp-iteration-output",
    "vasprun.xml": "vasp-xml-output",
    "CONTCAR": "vasp-final-structure",
    "EIGENVAL": "vasp-eigenvalues",
    "DOSCAR": "vasp-dos",
    "PROCAR": "vasp-projections",
    "CHGCAR": "vasp-charge-density",
    "WAVECAR": "vasp-wavefunctions",
}


def infer_role(path: Path) -> str:
    if path.name in ROLES:
        return ROLES[path.name]
    suffix = path.suffix.lower()
    if suffix in {".in", ".inp"}:
        return "qe-input-or-generic-input"
    if suffix in {".out", ".log"}:
        return "calculation-output-or-log"
    if suffix in {".xml", ".h5", ".hdf5"}:
        return "structured-output"
    if suffix in {".dat", ".csv", ".json"}:
        return "derived-or-tabular-data"
    return "unclassified"


def detect_code(names: set[str]) -> str:
    vasp = bool(names.intersection({"INCAR", "POSCAR", "OUTCAR", "vasprun.xml"}))
    qe = any(name.lower().endswith((".in", ".inp")) for name in names) or any("pwscf" in name.lower() for name in names)
    if vasp and qe:
        return "mixed"
    if vasp:
        return "vasp"
    if qe:
        return "qe"
    return "unknown"


def build_inventory(root: Path, max_files: int = 20000, hash_limit_bytes: int = 20 * 1024 * 1024) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    files = []
    for index, path in enumerate(sorted(root.rglob("*"))):
        if index >= max_files:
            raise ValueError(f"inventory exceeds max_files={max_files}")
        if path.is_symlink() or not path.is_file():
            continue
        stat = path.stat()
        relative = path.relative_to(root).as_posix()
        record = {
            "path": relative,
            "role": infer_role(path),
            "bytes": stat.st_size,
            "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
            "sha256": sha256_file(path) if stat.st_size <= hash_limit_bytes and path.name != "POTCAR" else None,
            "hash_status": "redacted-licensed" if path.name == "POTCAR" else ("present" if stat.st_size <= hash_limit_bytes else "skipped-size"),
        }
        files.append(record)
    names = {Path(item["path"]).name for item in files}
    return {
        "schema_version": "1.0",
        "root_label": root.name,
        "code": detect_code(names),
        "generated_utc": utc_now(),
        "file_count": len(files),
        "files": files,
    }
