from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

from .manifests import validation_errors
from .utils import sha256_file


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
    temporary.replace(path)


def _file_record(role: str, path: Path, label: str) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"missing file for role {role}: {path}")
    if path.name == "POTCAR":
        raise ValueError("POTCAR contents must not be recorded or passed to postprocessing tools")
    if not label or Path(label).is_absolute() or ".." in Path(label).parts:
        raise ValueError(f"unsafe shared file label for role {role}")
    return {"role": role, "path": label, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def _log_record(path: Path) -> dict[str, Any]:
    return {"path": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def _shared_command(
    command: list[str],
    work: Path,
    inputs: dict[str, Path],
    outputs: dict[str, Path],
) -> list[str]:
    """Redact runtime paths while preserving the argv shape needed for audit."""

    replacements = {str(work): "working-directory"}
    replacements.update((str(path.resolve()), path.name) for path in inputs.values())
    for path in outputs.values():
        replacements[str(path)] = str(path.relative_to(work))
    shared: list[str] = []
    for item in command:
        redacted = item
        for private, label in sorted(replacements.items(), key=lambda pair: len(pair[0]), reverse=True):
            redacted = redacted.replace(private, label)
        candidate = Path(redacted)
        if candidate.is_absolute():
            redacted = candidate.name
        elif "=" in redacted:
            prefix, value = redacted.split("=", 1)
            if Path(value).is_absolute():
                redacted = f"{prefix}={Path(value).name}"
        shared.append(redacted)
    return shared


def _output_path(work: Path, value: Path) -> Path:
    selected = value if value.is_absolute() else work / value
    selected = selected.resolve()
    try:
        selected.relative_to(work)
    except ValueError as exc:
        raise ValueError(f"expected output escapes working directory: {value}") from exc
    return selected


def run_external_command(
    *,
    execution_id: str,
    plan_id: str,
    step_id: str,
    backend: str,
    command: list[str],
    working_directory: Path,
    record_directory: Path,
    input_files: dict[str, Path],
    expected_outputs: dict[str, Path],
    timeout_s: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    if not command or not all(isinstance(item, str) and item and "\x00" not in item for item in command):
        raise ValueError("command must be a nonempty argv list of nonempty strings")
    if timeout_s < 1:
        raise ValueError("timeout_s must be positive")
    work = working_directory.resolve()
    if not work.is_dir():
        raise ValueError(f"working directory is not a directory: {work}")
    records = record_directory.resolve()
    outputs = {role: _output_path(work, path) for role, path in expected_outputs.items()}
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing:
        raise ValueError(f"refusing to overwrite existing outputs: {existing}")
    input_records = [_file_record(role, path, path.name) for role, path in sorted(input_files.items())]
    shared_command = _shared_command(command, work, input_files, outputs)

    base = {
        "schema_version": "1.0",
        "execution_id": execution_id,
        "plan_id": plan_id,
        "step_id": step_id,
        "backend": backend,
        "command": shared_command,
        "working_directory_label": "working-directory",
        "dry_run": dry_run,
        "status": "dry-run" if dry_run else "blocked",
        "started_utc": None,
        "finished_utc": None,
        "duration_s": None,
        "return_code": None,
        "inputs": input_records,
        "outputs": [],
        "stdout": None,
        "stderr": None,
        "limitations": [],
    }
    if dry_run:
        errors = validation_errors("execution", base)
        if errors:
            raise ValueError("generated dry-run record is invalid: " + "; ".join(errors))
        return base

    records.mkdir(parents=True, exist_ok=True)
    stdout_path = records / f"{execution_id}.stdout"
    stderr_path = records / f"{execution_id}.stderr"
    if stdout_path.exists() or stderr_path.exists():
        raise ValueError(f"refusing to overwrite execution logs for {execution_id}")

    started = _utc_now()
    clock = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=work,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        return_code = completed.returncode
        status = "succeeded" if return_code == 0 else "failed"
        limitations = [] if return_code == 0 else [f"tool returned nonzero exit code {return_code}"]
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        return_code = None
        status = "timed-out"
        limitations = [f"tool exceeded timeout_s={timeout_s}"]
    finished = _utc_now()
    duration = time.monotonic() - clock
    _write_bytes_atomic(stdout_path, stdout)
    _write_bytes_atomic(stderr_path, stderr)

    output_records = []
    missing_outputs = []
    for role, path in sorted(outputs.items()):
        if path.is_file():
            output_records.append(_file_record(role, path, str(path.relative_to(work))))
        else:
            missing_outputs.append(role)
    if missing_outputs:
        status = "failed" if status == "succeeded" else status
        limitations.append(f"missing expected outputs: {missing_outputs}")

    record = {
        **base,
        "status": status,
        "started_utc": started,
        "finished_utc": finished,
        "duration_s": duration,
        "return_code": return_code,
        "outputs": output_records,
        "stdout": _log_record(stdout_path),
        "stderr": _log_record(stderr_path),
        "limitations": limitations,
    }
    errors = validation_errors("execution", record)
    if errors:
        raise ValueError("generated execution record is invalid: " + "; ".join(errors))
    return record
