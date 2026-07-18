from __future__ import annotations

import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import time
from typing import Any

from . import __version__
from .electronic import (
    _check_maturity,
    _output_record,
    _refuse_existing_outputs,
    _source_record,
    _validated_dataset,
)
from .utils import utc_now, write_json_atomic


VESTA_MACOS_EXECUTABLE = Path("/Applications/VESTA/VESTA.app/Contents/MacOS/VESTA")
SURFACE_MODES = {"positive", "negative", "positive-negative"}


def resolve_vesta_executable(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        return candidate if candidate.is_file() else None
    for command in ("VESTA", "vesta"):
        resolved = shutil.which(command)
        if resolved:
            return Path(resolved).resolve()
    return VESTA_MACOS_EXECUTABLE if VESTA_MACOS_EXECUTABLE.is_file() else None


def _validate_rgb(color: tuple[int, int, int], label: str) -> tuple[int, int, int]:
    if len(color) != 3 or any(not isinstance(value, int) or value < 0 or value > 255 for value in color):
        raise ValueError(f"{label} must contain three integers within 0..255")
    return color


def configure_isosurfaces(
    project_text: str,
    *,
    level: float,
    mode: str,
    positive_color: tuple[int, int, int] = (255, 210, 0),
    negative_color: tuple[int, int, int] = (0, 200, 255),
    opacity_parallel: int = 160,
    opacity_perpendicular: int = 230,
    show_compass: bool = False,
) -> str:
    if not project_text.startswith("#VESTA_FORMAT_VERSION ") or "\nIMPORT_DENSITY 1\n" not in project_text:
        raise ValueError("VESTA project is missing a supported format header or imported density")
    if mode not in SURFACE_MODES:
        raise ValueError(f"unknown VESTA surface mode: {mode}")
    if not math.isfinite(level) or level <= 0.0:
        raise ValueError("isosurface level must be finite and positive")
    positive_color = _validate_rgb(positive_color, "positive_color")
    negative_color = _validate_rgb(negative_color, "negative_color")
    if not 0 <= opacity_parallel <= 255 or not 0 <= opacity_perpendicular <= 255:
        raise ValueError("VESTA opacities must be within 0..255")

    surfaces: list[tuple[int, tuple[int, int, int]]] = []
    if mode == "positive-negative":
        surfaces.append((0, positive_color))
    elif mode == "positive":
        surfaces.append((1, positive_color))
    elif mode == "negative":
        surfaces.append((2, negative_color))
    lines = ["ISURF"]
    for number, (surface_mode, color) in enumerate(surfaces, start=1):
        lines.append(
            f"{number:3d} {surface_mode:3d} {level:12.6g} "
            f"{color[0]:3d} {color[1]:3d} {color[2]:3d} {opacity_parallel:3d} {opacity_perpendicular:3d}"
        )
    lines.append("  0   0   0   0")
    replacement = "\n".join(lines) + "\n"
    configured, count = re.subn(r"(?ms)^ISURF\s*\n.*?(?=^TEX3P\s*$)", replacement, project_text, count=1)
    if count != 1:
        raise ValueError("VESTA project does not contain exactly one editable ISURF block")
    configured, surface_style_count = re.subn(
        r"(?m)^SURFS\s+.*$", "SURFS   0  1  1", configured, count=1
    )
    if surface_style_count != 1:
        raise ValueError("VESTA project does not contain a SURFS style record")
    configured, compass_count = re.subn(
        r"(?m)^COMPS\s+\d+\s*$", f"COMPS {1 if show_compass else 0}", configured, count=1
    )
    if compass_count != 1:
        raise ValueError("VESTA project does not contain a COMPS style record")
    return configured


def classify_conversion_result(return_code: int, stdout: str, stderr: str, project_text: str) -> bool:
    valid_project = (
        project_text.startswith("#VESTA_FORMAT_VERSION ")
        and "\nIMPORT_DENSITY 1\n" in project_text
        and "\nISURF\n" in project_text
    )
    if return_code == 0:
        return valid_project
    combined_log = f"{stdout}\n{stderr}"
    return return_code == 255 and "Saved data to:" in combined_log and valid_project


def configure_density_path(project_text: str, grid_path: Path) -> str:
    replacement = f"IMPORT_DENSITY 1\n+1.000000 {grid_path.resolve()}"
    configured, count = re.subn(
        r"(?m)^IMPORT_DENSITY 1\s*\n[^\n]+$",
        lambda _: replacement,
        project_text,
        count=1,
    )
    if count != 1:
        raise ValueError("VESTA project does not contain exactly one editable density import")
    return configured


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"VESTA export is not a valid PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width < 1 or height < 1:
        raise ValueError("VESTA export has invalid PNG dimensions")
    return width, height


def _convert_grid_to_project(executable: Path, grid: Path, project: Path, timeout_seconds: float) -> dict[str, Any]:
    command = [str(executable), "-nogui", "-i", str(grid), "-o", str(project)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"VESTA conversion timed out after {timeout_seconds:g} s") from exc
    project_text = project.read_text(encoding="utf-8", errors="replace") if project.is_file() else ""
    if not classify_conversion_result(completed.returncode, completed.stdout, completed.stderr, project_text):
        raise RuntimeError(
            "VESTA conversion failed closed: "
            f"exit={completed.returncode}, output_exists={project.is_file()}, saved_marker="
            f"{'Saved data to:' in (completed.stdout + completed.stderr)}"
        )
    return {
        "command": command,
        "raw_return_code": completed.returncode,
        "nonzero_success_quirk": completed.returncode == 255,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "project_text": project_text,
    }


def _export_project_image(
    executable: Path,
    project: Path,
    output: Path,
    *,
    export_scale: int,
    model_scale: float,
    rotations_degrees: tuple[float, float, float],
    timeout_seconds: float,
) -> dict[str, Any]:
    if export_scale < 1:
        raise ValueError("export_scale must be at least 1")
    if not math.isfinite(model_scale) or model_scale <= 0.0:
        raise ValueError("model_scale must be finite and positive")
    if not all(math.isfinite(value) for value in rotations_degrees):
        raise ValueError("VESTA rotations must be finite")
    command = [str(executable), "-open", str(project), "-flush"]
    for flag, angle in zip(("-rotate_x", "-rotate_y", "-rotate_z"), rotations_degrees):
        if angle:
            command.extend((flag, f"{angle:.12g}"))
    command.extend(("-scale", f"{model_scale:.12g}", "-export_img", f"scale={export_scale}", str(output)))

    log_path: Path | None = None
    process: subprocess.Popen[str] | None = None
    stable_observations = 0
    previous_size = -1
    export_ready = False
    deadline = time.monotonic() + timeout_seconds
    try:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", prefix="dftpost-vesta-", suffix=".log", delete=False) as log_handle:
            log_path = Path(log_handle.name)
            process = subprocess.Popen(command, stdout=log_handle, stderr=subprocess.STDOUT, text=True)
            while time.monotonic() < deadline:
                if output.is_file() and output.stat().st_size > 24:
                    current_size = output.stat().st_size
                    stable_observations = stable_observations + 1 if current_size == previous_size else 0
                    previous_size = current_size
                    if stable_observations >= 2:
                        _png_dimensions(output)
                        export_ready = True
                        break
                if process.poll() is not None and not output.is_file():
                    break
                time.sleep(0.1)
        if process is None:
            raise AssertionError("VESTA export process was not started")
        terminated_after_export = False
        if process.poll() is None:
            terminated_after_export = export_ready
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)
        if not export_ready:
            raise RuntimeError(f"VESTA image export did not produce a stable valid PNG within {timeout_seconds:g} s")
        width, height = _png_dimensions(output)
        log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path else ""
        return {
            "command": command,
            "raw_return_code": process.returncode,
            "terminated_after_verified_export": terminated_after_export,
            "log_tail": log_text[-8000:],
            "png_width": width,
            "png_height": height,
        }
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5.0)
        if log_path is not None and log_path.exists():
            log_path.unlink()


def render_vesta_isosurface(
    grid_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    field_kind: str,
    field_unit: str,
    level: float,
    level_unit: str,
    mode: str = "positive-negative",
    positive_color: tuple[int, int, int] = (255, 210, 0),
    negative_color: tuple[int, int, int] = (0, 200, 255),
    opacity_parallel: int = 160,
    opacity_perpendicular: int = 230,
    export_scale: int = 2,
    model_scale: float = 2.0,
    rotations_degrees: tuple[float, float, float] = (0.0, 0.0, 0.0),
    executable: Path | None = None,
    timeout_seconds: float = 30.0,
    figure_output: Path | None = None,
    maturity: str = "tool-integration-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    if not field_kind.strip() or not field_unit.strip() or not level_unit.strip():
        raise ValueError("field_kind, field_unit, and level_unit must be explicit and nonempty")
    if timeout_seconds <= 0.0 or not math.isfinite(timeout_seconds):
        raise ValueError("timeout_seconds must be finite and positive")
    grid_path = grid_path.resolve()
    if not grid_path.is_file():
        raise ValueError(f"grid file is missing: {grid_path}")
    selected_executable = resolve_vesta_executable(executable)
    if selected_executable is None:
        raise RuntimeError("TOOL_UNAVAILABLE: VESTA executable is required for structure-plus-isosurface rendering")

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    project_path = output_directory / "isosurface.vesta"
    analysis_path = output_directory / "vesta-isosurface.analysis.json"
    plot_metadata_path = output_directory / "vesta-isosurface.plot.json"
    dataset_path = output_directory / "vesta-isosurface.dataset.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "vesta-isosurface.png"
    _refuse_existing_outputs((project_path, analysis_path, plot_metadata_path, dataset_path, figure_path), overwrite)

    conversion = _convert_grid_to_project(selected_executable, grid_path, project_path, timeout_seconds)
    configured = configure_isosurfaces(
        conversion.pop("project_text"),
        level=level,
        mode=mode,
        positive_color=positive_color,
        negative_color=negative_color,
        opacity_parallel=opacity_parallel,
        opacity_perpendicular=opacity_perpendicular,
    )
    configured = configure_density_path(configured, grid_path)
    _write_text_atomic(project_path, configured)
    export = _export_project_image(
        selected_executable,
        project_path,
        figure_path,
        export_scale=export_scale,
        model_scale=model_scale,
        rotations_degrees=rotations_degrees,
        timeout_seconds=timeout_seconds,
    )
    format_match = re.match(r"#VESTA_FORMAT_VERSION\s+([^\s]+)", configured)
    project_format_version = format_match.group(1) if format_match else "unknown"
    limitations = [
        "The isosurface level, level unit, colors, opacity, scale, and view rotation are caller-declared visualization parameters; no physical threshold is inferred.",
        "The image is a VESTA rendering artifact; numerical claims must use the source grid or normalized tables rather than pixel appearance.",
        "For paired positive/negative rendering, VESTA project mode 0 applies VESTA's inverse-color convention to the negative surface; only the positive base color is explicit.",
        "VESTA may apply format-specific import conversions. In particular, native VASP charge-density imports require the caller to choose and record the level in VESTA-imported units.",
        "Panel assembly, arrows, annotations, and material-specific physical interpretation are intentionally outside this generic adapter.",
    ]
    analysis = {
        "schema_version": "1.0",
        "field_kind": field_kind,
        "field_unit": field_unit,
        "isosurface_level": level,
        "isosurface_level_unit": level_unit,
        "surface_mode": mode,
        "positive_color_rgb": list(positive_color),
        "negative_color_rgb": list(negative_color) if mode == "negative" else None,
        "negative_color_policy": "vesta-inverse-of-positive" if mode == "positive-negative" else ("explicit" if mode == "negative" else "not-used"),
        "opacity_parallel": opacity_parallel,
        "opacity_perpendicular": opacity_perpendicular,
        "rotations_degrees_xyz": list(rotations_degrees),
        "model_scale": model_scale,
        "export_scale": export_scale,
        "vesta_executable": str(selected_executable),
        "vesta_project_format_version": project_format_version,
        "conversion": conversion,
        "export": export,
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = {
        "schema_version": "1.0",
        "plot_type": "structure-plus-volumetric-isosurfaces",
        "backend": "VESTA CLI",
        "surface_mode": mode,
        "isosurface_level": level,
        "isosurface_level_unit": level_unit,
        "positive_color_rgb": list(positive_color),
        "negative_color_rgb": list(negative_color) if mode == "negative" else None,
        "negative_color_policy": "vesta-inverse-of-positive" if mode == "positive-negative" else ("explicit" if mode == "negative" else "not-used"),
        "png_dimensions": [export["png_width"], export["png_height"]],
        "output": _output_record(figure_path, "figure", "image/png"),
    }
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "real-space",
        "code": code,
        "maturity": maturity,
        "representation": "grid",
        "source_files": [_source_record(grid_path, "grid-field")],
        "dimensions": {"surface_count": 2 if mode == "positive-negative" else 1},
        "columns": [
            {"name": "field_value", "dtype": "float", "unit": field_unit, "role": "isosurface-source-field"},
        ],
        "data_files": [
            _output_record(project_path, "vesta-project", "text/plain"),
            _output_record(analysis_path, "tool-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "vesta-isosurface-render",
                "parameters": {"level": level, "level_unit": level_unit, "mode": mode},
                "input_columns": ["field_value"],
                "output_columns": [],
            }
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "vesta-project", "status": "pass", "message": "VESTA project header, density import, and isosurface block were validated."},
                {"id": "png-export", "status": "pass", "message": "A stable PNG with a valid signature and positive dimensions was exported."},
                {"id": "explicit-level-unit", "status": "pass", "message": "The caller supplied both isosurface level and level unit."},
            ],
        },
        "limitations": limitations,
        "provenance": {
            "producer": "dftpost.vesta-isosurface",
            "producer_version": __version__,
            "generated_utc": utc_now(),
            "tool_execution_ids": [],
        },
    }
    _validated_dataset(dataset, dataset_path)
    return {
        "project": project_path,
        "analysis": analysis_path,
        "plot_metadata": plot_metadata_path,
        "figure": figure_path,
        "dataset": dataset_path,
    }
