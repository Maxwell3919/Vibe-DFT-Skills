from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from .contracts import errors as contract_errors
from .privacy import privacy_errors


SCHEMA_VERSION = 2
EXPECTED_CAMPAIGN_COLUMNS = frozenset(
    {
        "record_id",
        "code",
        "code_version",
        "task_type",
        "system_class",
        "atom_count",
        "scientific_protocol_id",
        "configuration_id",
        "accepted",
        "acceptance_verified",
        "core_hours",
        "wall_time_s",
        "recorded_utc",
        "payload_json",
    }
)


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(path: Path) -> None:
    with closing(connect(path)) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            if not row["name"].startswith("sqlite_")
        }
        if tables:
            if "metadata" not in tables:
                raise ValueError(
                    "unsupported pre-versioned database; create a new v2 store "
                    "and explicitly convert privacy-safe records"
                )
            current = connection.execute(
                "SELECT value FROM metadata WHERE key='schema_version'"
            ).fetchone()
            if current is None or current["value"] != str(SCHEMA_VERSION):
                version = current["value"] if current is not None else "missing"
                raise ValueError(
                    f"unsupported database schema version: {version}; create a "
                    "new v2 store and explicitly convert privacy-safe records"
                )
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
                acceptance_verified INTEGER NOT NULL,
                core_hours REAL NOT NULL,
                wall_time_s REAL NOT NULL,
                recorded_utc TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_campaign_comparable
            ON campaign_records (
                code, code_version, task_type, system_class,
                atom_count, scientific_protocol_id, accepted,
                acceptance_verified, configuration_id
            );
                """
            )
            current = connection.execute(
                "SELECT value FROM metadata WHERE key='schema_version'"
            ).fetchone()
            if current is None:
                connection.execute("INSERT INTO metadata(key, value) VALUES('schema_version', ?)", (str(SCHEMA_VERSION),))
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(campaign_records)"
            ).fetchall()
        }
        if columns != EXPECTED_CAMPAIGN_COLUMNS:
            raise ValueError(
                "database declares schema v2 but campaign_records columns do not "
                "match the authenticated-acceptance store layout"
            )


def validate_record(record: object) -> list[str]:
    failures = contract_errors("campaign", record) + privacy_errors(record)
    if not isinstance(record, dict):
        return failures
    source_ref = record.get("source_run_ref")
    if isinstance(source_ref, dict):
        if source_ref.get("record_id") != record.get("run_manifest_id"):
            failures.append("source_run_ref.record_id must equal run_manifest_id")
        if source_ref.get("sha256") != record.get("source_manifest_sha256"):
            failures.append(
                "source_run_ref.sha256 must equal source_manifest_sha256"
            )
    outcome = record.get("outcome")
    if isinstance(outcome, dict) and outcome.get("status") in {
        "accepted",
        "rejected",
    }:
        failures.append(
            "accepted/rejected campaign ingestion requires production bundle "
            "verification and external human trust; this store API has no trust resolver"
        )
    return failures


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
                accepted, acceptance_verified, core_hours, wall_time_s,
                recorded_utc, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    0,
                    0,
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
              AND atom_count=? AND scientific_protocol_id=?
              AND accepted=1 AND acceptance_verified=1
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
