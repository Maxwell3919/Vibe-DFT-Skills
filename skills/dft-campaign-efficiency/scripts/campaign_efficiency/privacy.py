from __future__ import annotations

import re
from typing import Any


FORBIDDEN_KEYS = {
    "material_formula",
    "material_name",
    "project_name",
    "local_path",
    "absolute_path",
    "hostname",
    "host_name",
    "account",
    "account_name",
    "queue_name",
    "partition_name",
    "username",
    "password",
    "access_token",
    "api_key",
    "credential",
}

PRIVATE_PATH = re.compile(r"(?:^|\s)(?:/Users/|/home/|/Volumes/|[A-Za-z]:\\)")


def privacy_errors(value: Any, location: str = "<root>") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            child_location = f"{location}/{key}"
            if normalized in FORBIDDEN_KEYS:
                failures.append(f"{child_location}: forbidden private-identity field")
            failures.extend(privacy_errors(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(privacy_errors(child, f"{location}/{index}"))
    elif isinstance(value, str) and PRIVATE_PATH.search(value):
        failures.append(f"{location}: private absolute path is forbidden")
    return failures
