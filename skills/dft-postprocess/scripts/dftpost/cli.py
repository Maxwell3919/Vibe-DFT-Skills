from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .capabilities import detect_capabilities
from .inventory import build_inventory
from .manifests import build_artifact_manifest, validate_manifest
from .parsers import extract_summary
from .plotting import plot_table
from .utils import write_json_atomic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dftpost", description="Deterministic QE/VASP postprocessing foundation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--out", type=Path, required=True)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("root", type=Path)
    inventory.add_argument("--out", type=Path, required=True)
    inventory.add_argument("--max-files", type=int, default=20000)
    inventory.add_argument("--hash-limit-mb", type=float, default=20.0)

    summary = subparsers.add_parser("extract-summary")
    summary.add_argument("output", type=Path)
    summary.add_argument("--code", choices=("auto", "qe", "vasp"), default="auto")
    summary.add_argument("--out", type=Path, required=True)

    plot = subparsers.add_parser("plot-table")
    plot.add_argument("table", type=Path)
    plot.add_argument("--x", required=True)
    plot.add_argument("--y", required=True)
    plot.add_argument("--group")
    plot.add_argument("--xlabel", required=True)
    plot.add_argument("--ylabel", required=True)
    plot.add_argument("--title")
    plot.add_argument("--out", type=Path, required=True)
    plot.add_argument("--metadata-out", type=Path, required=True)

    validate = subparsers.add_parser("validate-manifest")
    validate.add_argument("kind", choices=("run", "artifact", "campaign", "recommendation"))
    validate.add_argument("manifest", type=Path)

    artifact = subparsers.add_parser("artifact-manifest")
    artifact.add_argument("--artifact-id", required=True)
    artifact.add_argument("--source-run-id", action="append", required=True)
    artifact.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
    artifact.add_argument("--artifact-type", required=True)
    artifact.add_argument("--status", choices=("complete", "partial", "failed", "blocked"), required=True)
    artifact.add_argument("--artifact-root", type=Path, required=True)
    artifact.add_argument("--data", action="append", default=[])
    artifact.add_argument("--figure", action="append", default=[])
    artifact.add_argument("--validation-status", choices=("pass", "warn", "block"), required=True)
    artifact.add_argument("--check", action="append", default=[])
    artifact.add_argument("--claim-boundary", action="append", default=[])
    artifact.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capabilities":
            write_json_atomic(args.out, detect_capabilities())
        elif args.command == "inventory":
            write_json_atomic(args.out, build_inventory(args.root, args.max_files, int(args.hash_limit_mb * 1024 * 1024)))
        elif args.command == "extract-summary":
            write_json_atomic(args.out, extract_summary(args.output, args.code))
        elif args.command == "plot-table":
            style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
            metadata = plot_table(args.table, args.out, args.x, args.y, args.group, args.xlabel, args.ylabel, args.title, style)
            metadata["command"] = list(sys.argv if argv is None else ["dftpost", *argv])
            write_json_atomic(args.metadata_out, metadata)
        elif args.command == "validate-manifest":
            errors = validate_manifest(args.kind, args.manifest)
            if errors:
                for item in errors:
                    print(item, file=sys.stderr)
                return 2
            print(f"PASS: {args.manifest}")
            return 0
        elif args.command == "artifact-manifest":
            manifest = build_artifact_manifest(
                args.artifact_id,
                args.source_run_id,
                args.code,
                args.artifact_type,
                args.status,
                args.artifact_root,
                args.data,
                args.figure,
                args.validation_status,
                args.check,
                args.claim_boundary,
                list(sys.argv if argv is None else ["dftpost", *argv]),
            )
            write_json_atomic(args.out, manifest)
        else:
            raise AssertionError(args.command)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
