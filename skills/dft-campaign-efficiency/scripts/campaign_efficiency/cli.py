from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from .contracts import calculation_codes
from .convert import campaign_from_run
from .recommend import recommendation
from .store import all_records, ingest, initialize
from strict_json import StrictJSONError, load_object


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dft-efficiency", description="Privacy-safe DFT campaign efficiency store")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--db", type=Path, required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--db", type=Path, required=True)
    ingest_parser.add_argument("record", type=Path)

    convert = subparsers.add_parser("from-run")
    convert.add_argument("run_manifest", type=Path)
    convert.add_argument("--system-class", required=True)
    convert.add_argument("--atom-count", type=int, required=True)
    convert.add_argument("--configuration-id", required=True)
    convert.add_argument("--accuracy-metrics", type=Path)
    convert.add_argument("--record-id")
    convert.add_argument("--out", type=Path, required=True)

    recommend = subparsers.add_parser("recommend")
    recommend.add_argument("--db", type=Path, required=True)
    recommend.add_argument("--code", choices=calculation_codes(), required=True)
    recommend.add_argument("--code-version", required=True)
    recommend.add_argument("--task-type", required=True)
    recommend.add_argument("--system-class", required=True)
    recommend.add_argument("--atom-count", type=int, required=True)
    recommend.add_argument("--protocol-id", required=True)
    recommend.add_argument("--out", type=Path, required=True)

    export = subparsers.add_parser("export")
    export.add_argument("--db", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except (OSError, ValueError, StrictJSONError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        if args.command == "init":
            initialize(args.db)
            print(args.db)
        elif args.command == "ingest":
            record = load_object(args.record, args.record.name)
            print(ingest(args.db, record))
        elif args.command == "from-run":
            accuracy = None
            if args.accuracy_metrics:
                accuracy = load_object(
                    args.accuracy_metrics,
                    args.accuracy_metrics.name,
                )
            result = campaign_from_run(
                args.run_manifest,
                args.system_class,
                args.atom_count,
                args.configuration_id,
                accuracy,
                args.record_id,
            )
            write_json(args.out, result)
            print(args.out)
        elif args.command == "recommend":
            result = recommendation(args.db, args.code, args.code_version, args.task_type, args.system_class, args.atom_count, args.protocol_id)
            write_json(args.out, result)
            print(args.out)
        elif args.command == "export":
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("w", encoding="utf-8") as handle:
                for record in all_records(args.db):
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            print(args.out)
        else:
            raise AssertionError(args.command)
    except (OSError, ValueError, StrictJSONError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
