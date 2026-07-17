from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from .contracts import errors as contract_errors
from .privacy import privacy_errors


SCHEMA_VERSION = 1


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(path: Path) -> None:
    with closing(connect(path)) as connection:
        with connection:
            connection.executescript(
                """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS campaign_records (
                record_id TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                code_version TEXT NOT NULL,
                task_type TEXT NOT NULL,
                system_class TEXT NOT NULL,
                atom_count INTEGER NOT NULL,
                scientific_protocol_id TEXT NOT NULL,
                configuration_id TEXT NOT NULL,
                accepted INTEGER NOT NULL,
                core_hours REAL NOT NULL,
                wall_time_s REAL NOT NULL,
                recorded_utc TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_campaign_comparable
            ON campaign_records (
                code, code_version, task_type, system_class,
                atom_count, scientific_protocol_id, accepted, configuration_id
            );
                """
            )
            current = connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if current is None:
                connection.execute("INSERT INTO metadata(key, value) VALUES('schema_version', ?)", (str(SCHEMA_VERSION),))
            elif int(current["value"]) != SCHEMA_VERSION:
                raise ValueError(f"unsupported database schema version: {current['value']}")


def validate_record(record: object) -> list[str]:
    return contract_errors("campaign", record) + privacy_errors(record)


def ingest(path: Path, record: dict[str, Any]) -> str:
    failures = validate_record(record)
    if failures:
        raise ValueError("invalid campaign record: " + "; ".join(failures))
    initialize(path)
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with closing(connect(path)) as connection:
        with connection:
            existing = connection.execute("SELECT payload_json FROM campaign_records WHERE record_id=?", (record["record_id"],)).fetchone()
            if existing is not None:
                if existing["payload_json"] == payload:
                    return "already-present"
                raise ValueError(f"record id collision with different payload: {record['record_id']}")
            connection.execute(
                """
            INSERT INTO campaign_records(
                record_id, code, code_version, task_type, system_class,
                atom_count, scientific_protocol_id, configuration_id,
                accepted, core_hours, wall_time_s, recorded_utc, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["record_id"],
                    record["code"],
                    record["code_version"],
                    record["task_type"],
                    record["system_class"],
                    record["atom_count"],
                    record["scientific_protocol_id"],
                    record["configuration_id"],
                    int(record["outcome"]["scientifically_accepted"]),
                    record["metrics"]["core_hours"],
                    record["metrics"]["wall_time_s"],
                    record["recorded_utc"],
                    payload,
                ),
            )
    return "inserted"


def comparable_records(
    path: Path,
    code: str,
    code_version: str,
    task_type: str,
    system_class: str,
    atom_count: int,
    protocol_id: str,
) -> list[dict[str, Any]]:
    initialize(path)
    with closing(connect(path)) as connection:
        rows = connection.execute(
            """
            SELECT payload_json FROM campaign_records
            WHERE code=? AND code_version=? AND task_type=? AND system_class=?
              AND atom_count=? AND scientific_protocol_id=? AND accepted=1
            ORDER BY recorded_utc, record_id
            """,
            (code, code_version, task_type, system_class, atom_count, protocol_id),
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def all_records(path: Path) -> Iterable[dict[str, Any]]:
    initialize(path)
    with closing(connect(path)) as connection:
        rows = connection.execute("SELECT payload_json FROM campaign_records ORDER BY recorded_utc, record_id").fetchall()
    for row in rows:
        yield json.loads(row["payload_json"])
