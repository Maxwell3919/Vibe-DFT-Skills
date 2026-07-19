"""Built-in semantic evaluators for official-source and evidence records.

This module is deliberately pure.  It reads only the frozen context mappings
supplied by the bundle dispatcher, never opens a path, imports a selected
adapter, or treats a bundle-authored resolver receipt as an external trust
root.  A platform may inject already-verified adapter results only through the
``registry_snapshots`` context member.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Iterable, Mapping


HANDLER_ID = "bundle-semantics-evidence-v1"
# Consumed by the production dispatcher's fixed-module resolver.  Keep this an
# exact tuple so both evidence contracts are routed without permitting bundle
# data to select an evaluator.
CONTRACT_NAMES = ("official-source-record", "evidence-record")
VALID_STATUS = frozenset({"pass", "fail", "blocked"})
ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s=,:;()\[\]{}\"'])(?:/Users/|/home/|/private/|/tmp/|"
    r"/Volumes/|/scratch/|/gpfs/|/lustre/|/mnt/|/work/|/project/)"
    r"|(?:^|[\s=,:;()\[\]{}\"'])[A-Za-z]:[\\/]"
)
SECRET_TEXT = re.compile(
    r"(?:password|passwd|api[_-]?key|access[_-]?token|secret|bearer)\s*[:=]",
    re.IGNORECASE,
)
HTTPS_LOCATOR = re.compile(
    r"^https://(?P<authority>[A-Za-z0-9.-]+(?::443)?)(?P<path>/[^?#]*)?$"
)
PRIVATE_KEYS = frozenset(
    {
        "access_key",
        "access_token",
        "api_key",
        "authorization_token",
        "cookie",
        "host_name",
        "hostname",
        "password",
        "passwd",
        "private_key",
        "secret",
        "secret_key",
        "token",
        "user_name",
        "username",
    }
)


def _result(
    obligation_id: str,
    status: str,
    finding_codes: Iterable[str] = (),
    *,
    location: str = "/",
    message: str,
) -> dict[str, Any]:
    if status not in VALID_STATUS:
        raise ValueError("invalid internal obligation status")
    return {
        "obligation_id": obligation_id,
        "status": status,
        "finding_codes": sorted(set(finding_codes)),
        "location": location,
        "message": message,
        "handler_id": HANDLER_ID,
    }


def _pass(obligation_id: str, location: str, message: str) -> dict[str, Any]:
    return _result(obligation_id, "pass", location=location, message=message)


def _fail(
    obligation_id: str,
    code: str,
    location: str,
    message: str,
) -> dict[str, Any]:
    return _result(
        obligation_id,
        "fail",
        [code],
        location=location,
        message=message,
    )


def _blocked(
    obligation_id: str,
    code: str,
    location: str,
    message: str,
) -> dict[str, Any]:
    return _result(
        obligation_id,
        "blocked",
        [code],
        location=location,
        message=message,
    )


def _mapping(value: object) -> Mapping[Any, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any] | tuple[Any, ...]:
    """Accept parsed JSON arrays and the dispatcher's frozen tuple view."""

    return value if isinstance(value, (list, tuple)) else ()


def _view_data(wrapper: Mapping[Any, Any]) -> Mapping[str, Any]:
    data = _mapping(wrapper.get("data"))
    contract_name = wrapper.get("contract_name")
    schema_version = wrapper.get("schema_version")
    if (
        not isinstance(contract_name, str)
        or not isinstance(schema_version, str)
        or data.get("contract_name") != contract_name
        or data.get("schema_version") != schema_version
    ):
        return {}
    id_field = {
        "official-source-record": "source_record_id",
        "evidence-record": "evidence_id",
    }.get(contract_name)
    if id_field is not None and data.get(id_field) != wrapper.get("record_id"):
        return {}
    return data


def _record(context: Mapping[str, Any]) -> Mapping[str, Any]:
    wrapper = _mapping(context.get("current_record"))
    if (
        wrapper.get("integrity_verified_active") is not True
        or wrapper.get("lifecycle") != "active"
    ):
        return {}
    return _view_data(wrapper)


def _record_index(context: Mapping[str, Any]) -> int | None:
    value = context.get("current_record_index")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _record_table(context: Mapping[str, Any]) -> Mapping[Any, Any]:
    return _mapping(context.get("records_by_identity"))


def _artifacts(context: Mapping[str, Any]) -> Mapping[Any, Any]:
    return _mapping(context.get("artifacts_by_label"))


def _core_checks(context: Mapping[str, Any]) -> Mapping[Any, Any]:
    return _mapping(context.get("core_checks"))


def _snapshots(context: Mapping[str, Any]) -> Mapping[Any, Any]:
    return _mapping(context.get("registry_snapshots"))


def _record_entry(value: object) -> tuple[Mapping[str, Any], str | None, int | None]:
    wrapper = _mapping(value)
    data = _view_data(wrapper)
    digest = wrapper.get("raw_sha256")
    digest_value = digest if isinstance(digest, str) else None
    index = wrapper.get("index")
    index_value = index if isinstance(index, int) and not isinstance(index, bool) else None
    if (
        wrapper.get("integrity_verified_active") is not True
        or wrapper.get("lifecycle") != "active"
        or not data
    ):
        return {}, None, index_value
    return data, digest_value, index_value


def _resolve_ref(
    ref: object,
    context: Mapping[str, Any],
) -> tuple[Mapping[str, Any], str | None, int | None] | None:
    candidate = _mapping(ref)
    contract = candidate.get("contract_name")
    version = candidate.get("schema_version")
    record_id = candidate.get("record_id")
    if not all(isinstance(item, str) for item in (contract, version, record_id)):
        return None
    table = _record_table(context)
    wrapped = table.get((contract, version, record_id))
    if wrapped is None:
        return None
    view = _mapping(wrapped)
    if (
        view.get("contract_name") != contract
        or view.get("schema_version") != version
        or view.get("record_id") != record_id
    ):
        return None
    return _record_entry(wrapped)


def _ref_result(
    obligation_id: str,
    ref: object,
    context: Mapping[str, Any],
    *,
    location: str,
    role: str,
    contract_name: str | None = None,
    require_preexisting: bool = False,
    unresolved_code: str,
    mismatch_code: str,
) -> dict[str, Any]:
    candidate = _mapping(ref)
    if candidate.get("role") != role or (
        contract_name is not None and candidate.get("contract_name") != contract_name
    ):
        return _fail(
            obligation_id,
            mismatch_code,
            location,
            "The record reference role or contract does not match this semantic edge.",
        )
    resolved = _resolve_ref(candidate, context)
    if resolved is None:
        return _blocked(
            obligation_id,
            unresolved_code,
            location,
            "The referenced immutable record is not available with verified active contract integrity.",
        )
    _data, digest, target_index = resolved
    if digest is None:
        return _blocked(
            obligation_id,
            unresolved_code,
            location,
            "The target record has no contract-integrity-verified exact-byte digest.",
        )
    if candidate.get("sha256") != digest:
        return _fail(
            obligation_id,
            mismatch_code,
            location,
            "The record reference digest does not match the target raw bytes.",
        )
    if require_preexisting:
        current_index = _record_index(context)
        if current_index is None or target_index is None:
            return _blocked(
                obligation_id,
                unresolved_code,
                location,
                "Topological record indices are unavailable.",
            )
        if target_index >= current_index:
            return _fail(
                obligation_id,
                mismatch_code,
                location,
                "The immutable reference does not point to an earlier record.",
            )
    return _pass(obligation_id, location, "The immutable record reference resolves.")


def _combine(
    obligation_id: str,
    results: Iterable[dict[str, Any]],
    *,
    location: str,
    success_message: str,
) -> dict[str, Any]:
    rows = list(results)
    failed = [row for row in rows if row["status"] == "fail"]
    blocked = [row for row in rows if row["status"] == "blocked"]
    selected = failed or blocked
    if not selected:
        return _pass(obligation_id, location, success_message)
    status = "fail" if failed else "blocked"
    codes = {
        code
        for row in selected
        for code in row.get("finding_codes", [])
        if isinstance(code, str)
    }
    return _result(
        obligation_id,
        status,
        codes,
        location=location,
        message="One or more required semantic edges are unresolved or inconsistent.",
    )


def _artifact_result(
    obligation_id: str,
    file_ref: object,
    context: Mapping[str, Any],
    *,
    location: str,
    unresolved_code: str,
    mismatch_code: str,
) -> dict[str, Any]:
    ref = _mapping(file_ref)
    if ref.get("availability") != "present":
        return _pass(obligation_id, location, "No present artifact is claimed at this edge.")
    label = ref.get("label")
    if not isinstance(label, str):
        return _fail(obligation_id, mismatch_code, location, "The artifact label is invalid.")
    actual = _mapping(_artifacts(context).get(label))
    if not actual:
        return _blocked(
            obligation_id,
            unresolved_code,
            location,
            "The present artifact is absent from the exact-byte-verified artifact index.",
        )
    if actual.get("integrity_verified") is not True:
        return _blocked(
            obligation_id,
            unresolved_code,
            location,
            "The artifact view has not passed exact-byte integrity verification.",
        )
    digest = actual.get("raw_sha256")
    size = actual.get("bytes")
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
    ):
        return _blocked(
            obligation_id,
            unresolved_code,
            location,
            "The artifact index lacks a verified exact-byte digest or byte count.",
        )
    if digest != ref.get("sha256") or size != ref.get("bytes"):
        return _fail(
            obligation_id,
            mismatch_code,
            location,
            "Artifact digest or byte count differs from the exact indexed bytes.",
        )
    return _pass(obligation_id, location, "The present artifact raw bytes resolve.")


def _core_result(
    obligation_id: str,
    context: Mapping[str, Any],
    keys: tuple[str, ...],
    *,
    location: str,
    blocked_code: str,
    fail_code: str,
) -> dict[str, Any]:
    checks = _core_checks(context)
    value: object = None
    for key in keys:
        if key in checks:
            value = checks[key]
            break
    if isinstance(value, str):
        status = value
    else:
        status = _mapping(value).get("status")
    if status == "pass":
        return _pass(obligation_id, location, "The required core bundle check passed.")
    if status == "fail":
        return _fail(obligation_id, fail_code, location, "The core bundle check failed.")
    return _blocked(
        obligation_id,
        blocked_code,
        location,
        "The required core bundle check is unavailable or unresolved.",
    )


def _privacy_safe(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in PRIVATE_KEYS or not _privacy_safe(child):
                return False
    elif isinstance(value, (list, tuple)):
        return all(_privacy_safe(item) for item in value)
    elif isinstance(value, str):
        if ABSOLUTE_PATH.search(value) or SECRET_TEXT.search(value):
            return False
    return True


def _authority_entry(context: Mapping[str, Any]) -> Mapping[str, Any]:
    authority = _mapping(_record(context).get("authority"))
    registry_id = authority.get("authority_registry_id")
    authorities = _mapping(_snapshots(context).get("official_source_authorities"))
    entry = _mapping(authorities.get(registry_id))
    identity_policy = _mapping(entry.get("content_identity_policy"))
    if (
        entry.get("lifecycle") != "active"
        or identity_policy.get("mode")
        not in {
            "platform-adapter-only",
            "canonical-pinned-open-snapshot-or-platform-adapter",
        }
        or identity_policy.get("unpinned_action") != "adapter-required"
    ):
        return {}
    return entry


def _locator_matches(url: object, entry: Mapping[str, Any]) -> bool:
    if not isinstance(url, str):
        return False
    match = HTTPS_LOCATOR.fullmatch(url)
    if match is None:
        return False
    origin = f"https://{match.group('authority')}"
    path = match.group("path") or "/"
    segments = path.split("/")
    if (
        "%" in path
        or "\\" in path
        or "//" in path
        or any(item in {".", ".."} for item in segments)
    ):
        return False
    policy = _mapping(entry.get("locator_policy"))
    origins = policy.get("allowed_origins")
    prefixes = policy.get("allowed_path_prefixes")
    if not isinstance(origins, (list, tuple)) or not isinstance(
        prefixes, (list, tuple)
    ):
        return False
    if not all(isinstance(item, str) for item in (*origins, *prefixes)):
        return False
    return origin in origins and any(path.startswith(prefix) for prefix in prefixes)


def _authority_match(record: Mapping[str, Any], entry: Mapping[str, Any]) -> bool:
    authority = _mapping(record.get("authority"))
    retrieval = _mapping(record.get("retrieval"))
    kinds = entry.get("source_kinds")
    return (
        isinstance(kinds, (list, tuple))
        and authority.get("source_kind") in kinds
        and _locator_matches(authority.get("canonical_url"), entry)
        and _locator_matches(retrieval.get("retrieval_url"), entry)
    )


def _version_match(record: Mapping[str, Any], entry: Mapping[str, Any]) -> bool:
    declared = record.get("version_scope")
    allowed = entry.get("version_scopes")
    if isinstance(allowed, (list, tuple)):
        return declared in allowed
    return declared == entry.get("version_scope")


def _adapter_result(record: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]:
    content = _mapping(record.get("content"))
    adapter = _mapping(content.get("trust_adapter"))
    adapters = _mapping(_snapshots(context).get("external_trust_adapter_results"))
    by_adapter = _mapping(adapters.get(adapter.get("adapter_registry_id")))
    return _mapping(by_adapter.get(adapter.get("opaque_handle")))


def _official_authority(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    entry = _authority_entry(context)
    if not entry:
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_AUTHORITY_REGISTRY_UNRESOLVED",
            "/authority",
            "The platform authority registry snapshot has no matching entry.",
        )
    if not _authority_match(record, entry):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MISMATCH",
            "/authority",
            "Official source kind or URL differs from the trusted registry entry.",
        )
    return _pass(obligation_id, "/authority", "The official authority registry entry matches.")


def _official_provider(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    entry = _authority_entry(context)
    if not entry:
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_PROVIDER_REGISTRY_UNRESOLVED",
            "/authority/provider_id",
            "The trusted provider registry entry is unavailable.",
        )
    provider = _mapping(record.get("authority")).get("provider_id")
    if provider != entry.get("provider_id"):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_PROVIDER_REGISTRY_MISMATCH",
            "/authority/provider_id",
            "The declared provider differs from the trusted authority entry.",
        )
    return _pass(obligation_id, "/authority/provider_id", "The official provider matches.")


def _official_content_hash(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    content = _mapping(record.get("content"))
    status = content.get("status")
    if status == "embedded-open":
        row = _artifact_result(
            obligation_id,
            content.get("artifact"),
            context,
            location="/content/artifact",
            unresolved_code="OFFICIAL_SOURCE_PRESENT_ARTIFACT_UNRESOLVED",
            mismatch_code="OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MISMATCH",
        )
        artifact = _mapping(content.get("artifact"))
        if row["status"] == "pass" and (
            content.get("raw_sha256") != artifact.get("sha256")
            or content.get("bytes") != artifact.get("bytes")
        ):
            return _fail(
                obligation_id,
                "OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MISMATCH",
                "/content",
                "The content digest metadata differs from the embedded artifact reference.",
            )
        return row
    if status == "externally-resolved":
        result = _adapter_result(record, context)
        if not result:
            return _blocked(
                obligation_id,
                "OFFICIAL_SOURCE_EXTERNAL_TRUST_REQUIRED",
                "/content/trust_adapter",
                "Exact external content bytes require a platform-injected trust result.",
            )
        if (
            result.get("raw_sha256") != content.get("raw_sha256")
            or result.get("bytes") != content.get("bytes")
        ):
            return _fail(
                obligation_id,
                "OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MISMATCH",
                "/content",
                "The trusted external digest differs from the declared content digest.",
            )
        return _pass(obligation_id, "/content", "The external exact-byte digest matches.")
    return _blocked(
        obligation_id,
        "OFFICIAL_SOURCE_CONTENT_UNRESOLVED",
        "/content",
        "No exact source content is available for a positive documented claim.",
    )


def _official_present_artifact(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    content = _mapping(_record(context).get("content"))
    if content.get("status") != "embedded-open":
        return _pass(obligation_id, "/content/artifact", "No embedded source artifact is claimed.")
    return _artifact_result(
        obligation_id,
        content.get("artifact"),
        context,
        location="/content/artifact",
        unresolved_code="OFFICIAL_SOURCE_PRESENT_ARTIFACT_UNRESOLVED",
        mismatch_code="OFFICIAL_SOURCE_PRESENT_ARTIFACT_HASH_MISMATCH",
    )


def _official_pinned_snapshot(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    content = _mapping(record.get("content"))
    if content.get("status") != "embedded-open":
        return _pass(
            obligation_id,
            "/content/pinned_source_ref",
            "No embedded open source snapshot is claimed.",
        )
    entry = _authority_entry(context)
    identity_policy = _mapping(entry.get("content_identity_policy"))
    snapshot = _mapping(entry.get("canonical_snapshot"))
    manifest_digest = snapshot.get("manifest_raw_sha256")
    if (
        identity_policy.get("mode")
        != "canonical-pinned-open-snapshot-or-platform-adapter"
        or snapshot.get("integrity_verified") is not True
        or not isinstance(manifest_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest_digest) is None
    ):
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_CANONICAL_SNAPSHOT_UNAVAILABLE",
            "/content/pinned_source_ref",
            "The canonical snapshot manifest is absent or lacks verified exact-byte integrity.",
        )
    ref = _mapping(content.get("pinned_source_ref"))
    authority = _mapping(record.get("authority"))
    if (
        ref.get("authority_registry_id") != authority.get("authority_registry_id")
        or ref.get("snapshot_id") != snapshot.get("snapshot_id")
    ):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_CANONICAL_SNAPSHOT_REF_MISMATCH",
            "/content/pinned_source_ref",
            "The source reference does not identify the canonical authority snapshot.",
        )
    sources = _mapping(snapshot.get("sources_by_id"))
    source = _mapping(sources.get(ref.get("source_id")))
    if not source:
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_CANONICAL_SNAPSHOT_REF_MISMATCH",
            "/content/pinned_source_ref/source_id",
            "The pinned source ID is not present in the verified canonical snapshot.",
        )
    expected = {
        "canonical_url": authority.get("canonical_url"),
        "version_scope": record.get("version_scope"),
        "raw_sha256": content.get("raw_sha256"),
        "bytes": content.get("bytes"),
    }
    if any(source.get(key) != value for key, value in expected.items()):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_CANONICAL_SNAPSHOT_CONTENT_MISMATCH",
            "/content",
            "The canonical source URL, version, digest, or byte count differs from the pinned snapshot.",
        )
    return _pass(
        obligation_id,
        "/content/pinned_source_ref",
        "The embedded source bytes match the verified canonical snapshot pin.",
    )


def _resolver_ref(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    content = _mapping(_record(context).get("content"))
    if content.get("status") != "externally-resolved":
        return _pass(obligation_id, "/content/resolver_record_ref", "No external resolver is required.")
    return _ref_result(
        obligation_id,
        content.get("resolver_record_ref"),
        context,
        location="/content/resolver_record_ref",
        role="official-source-resolver",
        contract_name="evidence-record",
        require_preexisting=True,
        unresolved_code="OFFICIAL_SOURCE_RESOLVER_REF_UNRESOLVED",
        mismatch_code="OFFICIAL_SOURCE_RESOLVER_REF_MISMATCH",
    )


def _resolver_record(context: Mapping[str, Any]) -> Mapping[str, Any]:
    content = _mapping(_record(context).get("content"))
    resolved = _resolve_ref(content.get("resolver_record_ref"), context)
    return resolved[0] if resolved is not None else {}


def _official_resolver_evidence(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    content = _mapping(_record(context).get("content"))
    if content.get("status") != "externally-resolved":
        return _pass(obligation_id, "/content/resolver_record_ref", "Resolver evidence is not required.")
    receipt = _resolver_record(context)
    observation = _mapping(receipt.get("observation"))
    observer = _mapping(receipt.get("observed_by"))
    limits = _mapping(receipt.get("authority_limits"))
    artifacts = receipt.get("artifacts")
    receipt_artifacts = _sequence(artifacts)
    valid_receipt = any(
        _mapping(item).get("role") == "resolver-receipt"
        and _mapping(item).get("availability") == "present"
        for item in receipt_artifacts
    )
    if not (
        receipt.get("contract_name") == "evidence-record"
        and receipt.get("evidence_kind") in {"artifact-integrity", "provenance-observation"}
        and receipt.get("status") == "present"
        and observation.get("result") in {"pass", "observed"}
        and observer.get("actor_type") == "deterministic-tool"
        and limits.get("may_establish_external_source_authority") is False
        and valid_receipt
    ):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_RESOLVER_EVIDENCE_INVALID",
            "/content/resolver_record_ref",
            "The resolver provenance record is not a bounded deterministic receipt.",
        )
    rows = [
        _artifact_result(
            obligation_id,
            item,
            context,
            location="/content/resolver_record_ref/artifacts",
            unresolved_code="OFFICIAL_SOURCE_RESOLVER_RECEIPT_UNRESOLVED",
            mismatch_code="OFFICIAL_SOURCE_RESOLVER_RECEIPT_HASH_MISMATCH",
        )
        for item in receipt_artifacts
        if _mapping(item).get("role") == "resolver-receipt"
    ]
    return _combine(
        obligation_id,
        rows,
        location="/content/resolver_record_ref",
        success_message="The resolver provenance receipt has verified exact-byte integrity.",
    )


def _official_resolver_not_trust(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    content = _mapping(_record(context).get("content"))
    if content.get("status") != "externally-resolved":
        return _pass(obligation_id, "/content", "No external resolver receipt is present.")
    receipt = _resolver_record(context)
    limits = _mapping(receipt.get("authority_limits"))
    if limits.get("may_establish_external_source_authority") is not False:
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_RESOLVER_RECEIPT_SELF_AUTHORIZING",
            "/content/resolver_record_ref",
            "A bundle-authored receipt cannot establish external source authority.",
        )
    if not _adapter_result(_record(context), context):
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_EXTERNAL_TRUST_REQUIRED",
            "/content/trust_adapter",
            "Resolver provenance alone cannot establish external source trust.",
        )
    return _pass(obligation_id, "/content/resolver_record_ref", "The receipt remains non-authoritative.")


def _official_external_adapter(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    content = _mapping(record.get("content"))
    if content.get("status") != "externally-resolved":
        return _pass(obligation_id, "/content/trust_adapter", "External source trust is not required.")
    adapter = _mapping(content.get("trust_adapter"))
    result = _adapter_result(record, context)
    if not result or result.get("status") in {None, "unavailable", "unknown"}:
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_EXTERNAL_TRUST_REQUIRED",
            "/content/trust_adapter",
            "A platform-injected external trust result is required.",
        )
    authority = _mapping(record.get("authority"))
    expected = {
        "adapter_registry_id": adapter.get("adapter_registry_id"),
        "opaque_handle": adapter.get("opaque_handle"),
        "authority_registry_id": authority.get("authority_registry_id"),
        "provider_id": authority.get("provider_id"),
        "canonical_url": authority.get("canonical_url"),
        "version_scope": record.get("version_scope"),
        "raw_sha256": content.get("raw_sha256"),
        "bytes": content.get("bytes"),
    }
    if result.get("status") != "verified" or any(
        result.get(key) != value for key, value in expected.items()
    ):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_EXTERNAL_TRUST_MISMATCH",
            "/content/trust_adapter",
            "The injected trust result does not match authority, version, or content identity.",
        )
    return _pass(obligation_id, "/content/trust_adapter", "The platform trust result matches exactly.")


def _official_version(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    entry = _authority_entry(context)
    if not entry:
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_VERSION_REGISTRY_UNRESOLVED",
            "/version_scope",
            "The trusted authority version scope is unavailable.",
        )
    if not _version_match(record, entry):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_VERSION_SCOPE_MISMATCH",
            "/version_scope",
            "The declared source version scope differs from the trusted registry entry.",
        )
    return _pass(obligation_id, "/version_scope", "The official source version scope matches.")


def _official_status_ceiling(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    content = _mapping(record.get("content"))
    ceiling = record.get("claim_ceiling")
    status = content.get("status")
    if status in {"metadata-only", "unavailable", "unknown"}:
        valid = ceiling == "no_positive_claim"
    elif status == "externally-resolved" and ceiling == "documented_behavior_only":
        if not _adapter_result(record, context):
            return _blocked(
                obligation_id,
                "OFFICIAL_SOURCE_EXTERNAL_TRUST_REQUIRED",
                "/claim_ceiling",
                "The documented ceiling is conditional on external platform trust.",
            )
        valid = True
    elif status == "embedded-open" and ceiling == "documented_behavior_only":
        pin = _official_pinned_snapshot(obligation_id, context)
        if pin["status"] != "pass":
            return pin
        valid = True
    else:
        valid = ceiling in {"no_positive_claim", "documented_behavior_only"}
    if not valid:
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_STATUS_CLAIM_CEILING_MISMATCH",
            "/claim_ceiling",
            "The source resolution status cannot support the declared claim ceiling.",
        )
    return _pass(obligation_id, "/claim_ceiling", "The bounded claim ceiling matches source status.")


def _official_license(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    entry = _authority_entry(context)
    if not entry:
        return _blocked(
            obligation_id,
            "OFFICIAL_SOURCE_LICENSE_REGISTRY_UNRESOLVED",
            "/license",
            "Trusted license and redistribution metadata are unavailable.",
        )
    license_data = _mapping(record.get("license"))
    redistribution = entry.get("redistribution")
    terms_urls = entry.get("license_terms_urls")
    terms_url = license_data.get("terms_url")
    if (
        not isinstance(redistribution, (list, tuple))
        or not isinstance(terms_urls, (list, tuple))
        or not all(isinstance(item, str) for item in terms_urls)
        or license_data.get("status") != entry.get("license_status")
        or license_data.get("identifier") != entry.get("license_identifier")
        or (terms_url not in terms_urls if terms_urls else terms_url is not None)
        or license_data.get("redistribution") not in redistribution
    ):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MISMATCH",
            "/license",
            "License or redistribution metadata differs from the trusted registry entry.",
        )
    return _pass(obligation_id, "/license", "License and redistribution metadata match.")


def _official_restricted_not_embedded(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    license_data = _mapping(record.get("license"))
    content = _mapping(record.get("content"))
    if license_data.get("status") != "known-restricted":
        return _pass(obligation_id, "/content", "No restricted source content is declared.")
    artifact = _mapping(content.get("artifact"))
    indexed = _mapping(_artifacts(context).get(artifact.get("label")))
    indexed_metadata = _mapping(indexed.get("metadata"))
    if (
        content.get("status") == "embedded-open"
        or artifact.get("availability") == "present"
        or indexed_metadata.get("availability") == "present"
        or indexed.get("integrity_verified") is True
    ):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_RESTRICTED_CONTENT_EMBEDDED",
            "/content/artifact",
            "Restricted official source bytes must not be embedded in the bundle.",
        )
    return _pass(obligation_id, "/content/artifact", "Restricted source bytes are not embedded.")


def _official_metadata_only(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    content = _mapping(record.get("content"))
    if content.get("status") == "metadata-only" and record.get("claim_ceiling") != "no_positive_claim":
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_METADATA_ONLY_DOCUMENTED_CLAIM",
            "/claim_ceiling",
            "Metadata-only records cannot support a documented positive claim.",
        )
    return _pass(obligation_id, "/claim_ceiling", "Metadata-only claim limits are fail closed.")


def _official_parents(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    refs = _record(context).get("parent_source_refs")
    values = _sequence(refs)
    rows = [
        _ref_result(
            obligation_id,
            ref,
            context,
            location=f"/parent_source_refs/{index}",
            role="prior-official-source",
            contract_name="official-source-record",
            require_preexisting=True,
            unresolved_code="OFFICIAL_SOURCE_PARENT_REF_UNRESOLVED",
            mismatch_code="OFFICIAL_SOURCE_PARENT_REF_NOT_PREEXISTING",
        )
        for index, ref in enumerate(values)
    ]
    return _combine(
        obligation_id,
        rows,
        location="/parent_source_refs",
        success_message="All official source parents are earlier contract-integrity-verified records.",
    )


def _official_privacy(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    if not _privacy_safe(_record(context)):
        return _fail(
            obligation_id,
            "OFFICIAL_SOURCE_PRIVACY_UNSAFE",
            "/",
            "The official source metadata contains a private path, identifier, or credential-like value.",
        )
    return _pass(obligation_id, "/", "Official source metadata passes the privacy scan.")


def _evidence_refs(
    obligation_id: str,
    context: Mapping[str, Any],
    field: str,
    role: str,
    *,
    contract_name: str | None = None,
    require_preexisting: bool = False,
) -> dict[str, Any]:
    refs = _record(context).get(field)
    values = _sequence(refs)
    rows = [
        _ref_result(
            obligation_id,
            ref,
            context,
            location=f"/{field}/{index}",
            role=role,
            contract_name=contract_name,
            require_preexisting=require_preexisting,
            unresolved_code="EVIDENCE_RECORD_REF_UNRESOLVED",
            mismatch_code="EVIDENCE_RECORD_REF_MISMATCH",
        )
        for index, ref in enumerate(values)
    ]
    return _combine(
        obligation_id,
        rows,
        location=f"/{field}",
        success_message="All evidence record references resolve with the required role.",
    )


def _evidence_artifacts(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = _record(context).get("artifacts")
    values = _sequence(artifacts)
    present = [item for item in values if _mapping(item).get("availability") == "present"]
    rows = [
        _artifact_result(
            obligation_id,
            ref,
            context,
            location=f"/artifacts/{index}",
            unresolved_code="EVIDENCE_PRESENT_ARTIFACT_UNRESOLVED",
            mismatch_code="EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MISMATCH",
        )
        for index, ref in enumerate(values)
        if _mapping(ref).get("availability") == "present"
    ]
    if _record(context).get("status") == "present" and not present:
        return _fail(
            obligation_id,
            "EVIDENCE_PRESENT_ARTIFACT_UNRESOLVED",
            "/artifacts",
            "A present evidence record has no present content-addressed artifact.",
        )
    return _combine(
        obligation_id,
        rows,
        location="/artifacts",
        success_message="All present evidence artifacts match exact indexed bytes.",
    )


def _evidence_status(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    artifacts = record.get("artifacts")
    values = _sequence(artifacts)
    availability = {_mapping(item).get("availability") for item in values}
    status = record.get("status")
    expected = {
        "present": "present",
        "external": "external",
        "redacted": "redacted",
        "missing": "missing",
    }
    if status == "unknown":
        valid = not values
    else:
        valid = expected.get(status) in availability
    if not valid:
        return _fail(
            obligation_id,
            "EVIDENCE_STATUS_ARTIFACT_AVAILABILITY_MISMATCH",
            "/status",
            "Evidence status does not match artifact availability.",
        )
    return _pass(obligation_id, "/status", "Evidence status and artifact availability match.")


def _evidence_ceiling(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    record = _record(context)
    observation = _mapping(record.get("observation"))
    ceiling = record.get("claim_ceiling")
    if record.get("status") != "present" or observation.get("result") not in {"pass", "observed"}:
        allowed = {"no_positive_claim"}
    elif record.get("evidence_kind") in {"input-validation", "structure-observation"}:
        allowed = {"no_positive_claim", "documented_behavior_only", "input_gates_only"}
    elif record.get("evidence_kind") in {"convergence-study", "numerical-observation"}:
        allowed = {
            "no_positive_claim",
            "documented_behavior_only",
            "input_gates_only",
            "technical_run_gates_only",
            "numerical_candidate_only",
        }
    else:
        allowed = {
            "no_positive_claim",
            "documented_behavior_only",
            "input_gates_only",
            "technical_run_gates_only",
        }
    if ceiling not in allowed:
        return _fail(
            obligation_id,
            "EVIDENCE_KIND_RESULT_CLAIM_CEILING_MISMATCH",
            "/claim_ceiling",
            "Evidence kind, status, and result cannot support the declared claim ceiling.",
        )
    return _pass(obligation_id, "/claim_ceiling", "The evidence claim ceiling is bounded.")


def _evidence_nonhuman(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    actor_type = _mapping(_record(context).get("observed_by")).get("actor_type")
    if actor_type not in {"agent", "deterministic-tool"}:
        return _fail(
            obligation_id,
            "EVIDENCE_HUMAN_OBSERVER_FORBIDDEN",
            "/observed_by/actor_type",
            "Generic evidence records must remain explicitly non-human.",
        )
    return _pass(obligation_id, "/observed_by", "The observer is explicitly non-human.")


def _evidence_authority_limit(
    obligation_id: str,
    context: Mapping[str, Any],
    field: str,
    code: str,
) -> dict[str, Any]:
    if _mapping(_record(context).get("authority_limits")).get(field) is not False:
        return _fail(
            obligation_id,
            code,
            f"/authority_limits/{field}",
            "A generic evidence record cannot carry this authority.",
        )
    return _pass(obligation_id, f"/authority_limits/{field}", "The authority limit is fail closed.")


def _evidence_privacy(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    if not _privacy_safe(_record(context)):
        return _fail(
            obligation_id,
            "EVIDENCE_PRIVACY_UNSAFE",
            "/",
            "Evidence metadata contains a private path, identifier, or credential-like value.",
        )
    return _pass(obligation_id, "/", "Evidence metadata passes the privacy scan.")


OFFICIAL_HANDLERS: dict[str, Callable[[str, Mapping[str, Any]], dict[str, Any]]] = {
    "OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH": _official_authority,
    "OFFICIAL_SOURCE_PROVIDER_REGISTRY_MATCH": _official_provider,
    "OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MATCH": _official_content_hash,
    "OFFICIAL_SOURCE_PRESENT_ARTIFACT_HASH_RESOLVES": _official_present_artifact,
    "OFFICIAL_SOURCE_PINNED_CANONICAL_SNAPSHOT_MATCH": _official_pinned_snapshot,
    "OFFICIAL_SOURCE_RESOLVER_REF_HASH_RESOLVES": _resolver_ref,
    "OFFICIAL_SOURCE_RESOLVER_EVIDENCE_MATCH": _official_resolver_evidence,
    "OFFICIAL_SOURCE_RESOLVER_EVIDENCE_NOT_TRUST_ROOT": _official_resolver_not_trust,
    "OFFICIAL_SOURCE_EXTERNAL_TRUST_ADAPTER_VERIFIES": _official_external_adapter,
    "OFFICIAL_SOURCE_VERSION_SCOPE_MATCH": _official_version,
    "OFFICIAL_SOURCE_STATUS_CLAIM_CEILING_MATCH": _official_status_ceiling,
    "OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MATCH": _official_license,
    "OFFICIAL_SOURCE_RESTRICTED_CONTENT_NOT_EMBEDDED": _official_restricted_not_embedded,
    "OFFICIAL_SOURCE_METADATA_ONLY_NOT_DOCUMENTED_CLAIM": _official_metadata_only,
    "OFFICIAL_SOURCE_PARENT_REFS_PREEXIST_RECORD": _official_parents,
    "OFFICIAL_SOURCE_RECORD_REF_DAG_ACYCLIC": lambda oid, ctx: _core_result(
        oid,
        ctx,
        ("record-reference-dag", "record_reference_dag"),
        location="/",
        blocked_code="OFFICIAL_SOURCE_RECORD_REF_DAG_UNRESOLVED",
        fail_code="OFFICIAL_SOURCE_RECORD_REF_DAG_INVALID",
    ),
    "OFFICIAL_SOURCE_PRIVACY_LABELS_SAFE": _official_privacy,
}


EVIDENCE_HANDLERS: dict[str, Callable[[str, Mapping[str, Any]], dict[str, Any]]] = {
    "EVIDENCE_SUBJECT_REF_HASH_RESOLVES": lambda oid, ctx: _evidence_refs(
        oid, ctx, "subject_refs", "evidence-subject"
    ),
    "EVIDENCE_SOURCE_REF_HASH_RESOLVES": lambda oid, ctx: _evidence_refs(
        oid, ctx, "source_refs", "evidence-source"
    ),
    "EVIDENCE_PARENT_REF_HASH_RESOLVES": lambda oid, ctx: _evidence_refs(
        oid,
        ctx,
        "parent_evidence_refs",
        "parent-evidence",
        contract_name="evidence-record",
        require_preexisting=True,
    ),
    "EVIDENCE_REF_ROLE_MATCH": lambda oid, ctx: _combine(
        oid,
        (
            _evidence_refs(oid, ctx, "subject_refs", "evidence-subject"),
            _evidence_refs(oid, ctx, "source_refs", "evidence-source"),
            _evidence_refs(
                oid,
                ctx,
                "parent_evidence_refs",
                "parent-evidence",
                contract_name="evidence-record",
            ),
        ),
        location="/",
        success_message="All evidence reference roles match their semantic edges.",
    ),
    "EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MATCH": _evidence_artifacts,
    "EVIDENCE_STATUS_ARTIFACT_AVAILABILITY_MATCH": _evidence_status,
    "EVIDENCE_KIND_RESULT_CLAIM_CEILING_MATCH": _evidence_ceiling,
    "EVIDENCE_NONHUMAN_OBSERVER_REQUIRED": _evidence_nonhuman,
    "EVIDENCE_CANNOT_AUTHORIZE_EXECUTION": lambda oid, ctx: _evidence_authority_limit(
        oid, ctx, "may_authorize_execution", "EVIDENCE_EXECUTION_AUTHORITY_FORBIDDEN"
    ),
    "EVIDENCE_CANNOT_ACCEPT_SCIENCE": lambda oid, ctx: _evidence_authority_limit(
        oid, ctx, "may_accept_scientific_claim", "EVIDENCE_SCIENTIFIC_AUTHORITY_FORBIDDEN"
    ),
    "EVIDENCE_CANNOT_ESTABLISH_EXTERNAL_SOURCE_AUTHORITY": lambda oid, ctx: _evidence_authority_limit(
        oid,
        ctx,
        "may_establish_external_source_authority",
        "EVIDENCE_EXTERNAL_SOURCE_AUTHORITY_FORBIDDEN",
    ),
    "EVIDENCE_PARENT_REFS_PREEXIST_RECORD": lambda oid, ctx: _evidence_refs(
        oid,
        ctx,
        "parent_evidence_refs",
        "parent-evidence",
        contract_name="evidence-record",
        require_preexisting=True,
    ),
    "EVIDENCE_RECORD_REF_DAG_ACYCLIC": lambda oid, ctx: _core_result(
        oid,
        ctx,
        ("record-reference-dag", "record_reference_dag"),
        location="/",
        blocked_code="EVIDENCE_RECORD_REF_DAG_UNRESOLVED",
        fail_code="EVIDENCE_RECORD_REF_DAG_INVALID",
    ),
    "EVIDENCE_PRIVACY_LABELS_SAFE": _evidence_privacy,
}


HANDLERS = {**OFFICIAL_HANDLERS, **EVIDENCE_HANDLERS}


def evaluate(
    obligation_ids: Iterable[str],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate each requested obligation exactly once and never drop unknowns."""

    safe_context = context if isinstance(context, Mapping) else {}
    results: list[dict[str, Any]] = []
    for obligation_id in obligation_ids:
        if not isinstance(obligation_id, str):
            results.append(
                _blocked(
                    "INVALID_OBLIGATION_ID",
                    "OBLIGATION_HANDLER_UNAVAILABLE",
                    "/x-vibe-semantic-obligations",
                    "The obligation ID is not a string.",
                )
            )
            continue
        handler = HANDLERS.get(obligation_id)
        if handler is None:
            results.append(
                _blocked(
                    obligation_id,
                    "OBLIGATION_HANDLER_UNAVAILABLE",
                    "/x-vibe-semantic-obligations",
                    "No built-in evidence semantic handler is registered for this obligation.",
                )
            )
            continue
        if not _record(safe_context):
            results.append(
                _blocked(
                    obligation_id,
                    "OBLIGATION_CONTEXT_INCOMPLETE",
                    "/",
                    "The current record lacks a verified active contract-integrity view.",
                )
            )
            continue
        try:
            results.append(handler(obligation_id, safe_context))
        except (KeyError, TypeError, ValueError):
            results.append(
                _blocked(
                    obligation_id,
                    "OBLIGATION_CONTEXT_INCOMPLETE",
                    "/",
                    "The frozen semantic context is incomplete for this obligation.",
                )
            )
    return results


__all__ = ["CONTRACT_NAMES", "evaluate"]
