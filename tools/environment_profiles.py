#!/usr/bin/env python3
"""Validate fail-closed software environment and licensing profiles.

The registry is documentary: probes describe read-only checks but this module never
installs software, starts third-party executables, contacts services, or mutates a
runtime environment.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit

from registry_yaml import RegistryYAMLError, load_yaml_strict


SCHEMA_VERSION = "1.0"
CURRENT_PLATFORM = "macos"
CURRENT_ARCHITECTURE = "arm64"
CURRENT_PYTHON = (3, 14, 0)
CURRENT_SNAPSHOT_DATE = "2026-07-18"
CURRENT_MACHINE_CLASS = "apple-silicon-macos"

PROFILE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,2}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
ATTESTATION_ID = re.compile(r"^att-[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_KEY = re.compile(
    r"(?:^|[_-])(?:token|path|host|account|password|secret|credential|private[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)
LOCAL_LOCATION = re.compile(
    r"(?:^|[\s\"'=])(?:/Users/|/home/|/private/|/opt/|[A-Za-z]:\\|\$HOME|\$\{HOME\})"
)
REMOTE_IDENTITY = re.compile(r"(?:ssh|scp)://|\b[^\s/@]+@[^\s/]+(?::|\b)", re.IGNORECASE)
SECRET_ASSIGNMENT = re.compile(
    r"\b(?:token|host|account|password|secret|credential|api[_-]?key)\s*[:=]",
    re.IGNORECASE,
)

PROFILE_TYPES = {
    "binary-cli",
    "commercial-binary",
    "desktop-application",
    "ml-framework",
    "python-package",
    "simulation-engine",
}
ROLES = {
    "calculation-engine",
    "ml-potential-framework",
    "postprocess-tool",
    "scientific-workflow-tool",
    "structure-library",
    "visualization-tool",
}
PROFILE_ROLE_COMPATIBILITY = {
    "binary-cli": {"postprocess-tool"},
    "commercial-binary": {"calculation-engine", "postprocess-tool", "visualization-tool"},
    "desktop-application": {"visualization-tool"},
    "ml-framework": {"ml-potential-framework"},
    "python-package": {"postprocess-tool", "scientific-workflow-tool", "structure-library"},
    "simulation-engine": {"calculation-engine"},
}
SOURCE_TIERS = {"first-party-official", "third-party-community-referenced-by-official"}
LICENSE_CATEGORIES = {"custom", "mixed", "open-source", "restricted-proprietary"}
REDISTRIBUTION_VALUES = {
    "allowed-with-license",
    "component-dependent",
    "conditional",
    "not-established",
    "prohibited",
}
LICENSE_REDISTRIBUTION = {
    "open-source": {"allowed-with-license"},
    "mixed": {"component-dependent"},
    "custom": {"conditional", "not-established"},
    "restricted-proprietary": {"prohibited"},
}
PLATFORMS = {"linux", "macos", "windows"}
ARCHITECTURES = {"arm64", "x86_64"}
GPU_BACKENDS = {"cuda", "metal", "opencl", "rocm"}
ASSET_LICENSE_VALUES = {"not-applicable", "restricted", "separate-attestation", "unknown"}
PROBE_KINDS = {
    "application-metadata",
    "binary-banner",
    "cli-version",
    "manual-attestation",
    "python-metadata",
}
CURRENT_STATUSES = {
    "installed-compatible",
    "not-installed-compatible",
    "restricted-installed",
    "restricted-unavailable",
    "unsupported-architecture",
    "unsupported-hardware",
    "unsupported-platform",
    "unsupported-runtime",
    "unverified",
    "version-mismatch",
}
VALIDATION_LEVELS = (
    "planned",
    "environment-verified",
    "smoke-verified",
    "integration-verified",
    "scientifically-validated",
)
OFFICIAL_DOMAINS = {
    "catmap.readthedocs.io",
    "deepmodeling.com",
    "docs.deepmodeling.com",
    "docs.lammps.org",
    "fair-chem.github.io",
    "gaussian.com",
    "github.com",
    "gpumd.org",
    "lasphub.com",
    "mace-docs.readthedocs.io",
    "manual.gromacs.org",
    "nequip.readthedocs.io",
    "ovito.org",
    "phonopy.github.io",
    "pymatgen.org",
    "pypi.org",
    "pubs.acs.org",
    "rdkit.org",
    "schmeling.ac.rwth-aachen.de",
    "sobereva.com",
    "sourceforge.net",
    "vaspkit.com",
    "www.gaussian.com",
    "www.gpumd.org",
    "www.lasphub.com",
    "www.ovito.org",
    "www.rdkit.org",
    "www.sobereva.com",
    "www.vaspkit.com",
}
LEGACY_HTTP_DOMAINS = {"sobereva.com", "www.sobereva.com"}
# This is a reviewed, provider-specific identity snapshot rather than a domain
# allowlist. Adding a provider or changing any owner, project, path, query, or
# fragment therefore requires an explicit review and mapping update.
REVIEWED_PROVIDER_URLS: dict[str, frozenset[str]] = {
    "pymatgen-wrapper": frozenset(
        {
            "https://github.com/materialsproject/pymatgen/releases/latest",
            "https://pypi.org/project/pymatgen/",
        }
    ),
    "pymatgen-core": frozenset(
        {
            "https://github.com/materialsproject/pymatgen-core/releases/latest",
            "https://github.com/materialsproject/pymatgen-core/blob/main/pyproject.toml",
        }
    ),
    "rdkit-pypi": frozenset(
        {
            "https://github.com/rdkit/rdkit/releases/latest",
            "https://pypi.org/project/rdkit/",
            "https://www.rdkit.org/docs/Install.html",
        }
    ),
    "ovito-basic": frozenset(
        {
            "https://www.ovito.org/",
            "https://www.ovito.org/docs/current/python/introduction/installation.html",
            "https://www.ovito.org/manual/licenses/index.html",
        }
    ),
    "ovito-pro": frozenset(
        {
            "https://www.ovito.org/",
            "https://www.ovito.org/manual/licenses/index.html",
        }
    ),
    "phonopy-pypi": frozenset(
        {
            "https://pypi.org/project/phonopy/",
            "https://phonopy.github.io/phonopy/install.html",
            "https://github.com/phonopy/phonopy/blob/develop/LICENSE",
        }
    ),
    "vaspkit-linux-x64": frozenset(
        {
            "https://vaspkit.com/installation.html",
            "https://sourceforge.net/projects/vaspkit/files/Binaries/",
        }
    ),
    "vaspkit-macos-intel": frozenset(
        {
            "https://vaspkit.com/installation.html",
            "https://sourceforge.net/projects/vaspkit/files/Binaries/",
        }
    ),
    "multiwfn-official-linux-x64": frozenset(
        {
            "http://sobereva.com/multiwfn/download.html",
            "http://sobereva.com/multiwfn/overview.html",
        }
    ),
    "multiwfn-community-macos": frozenset(
        {"http://sobereva.com/multiwfn/download.html"}
    ),
    "lobster-5": frozenset(
        {
            "https://schmeling.ac.rwth-aachen.de/cohp/index.php?menuID=6",
            "https://schmeling.ac.rwth-aachen.de/cohp/index.php?fileID=19&menuID=603",
        }
    ),
    "catmap-v041": frozenset(
        {
            "https://github.com/SUNCAT-Center/catmap/releases/tag/v0.4.1",
            "https://github.com/SUNCAT-Center/catmap/blob/master/COPYING.txt",
            "https://catmap.readthedocs.io/en/latest/installation.html",
        }
    ),
    "gaussian-g16-c02": frozenset(
        {
            "https://gaussian.com/g16/",
            "https://gaussian.com/g16/g16_plat.pdf",
            "https://gaussian.com/wp-content/uploads/dl/cn_com.pdf",
        }
    ),
    "gromacs-cpu": frozenset(
        {
            "https://manual.gromacs.org/current/release-notes/2026/2026.3.html",
            "https://manual.gromacs.org/documentation/current/install-guide/index.html",
            "https://manual.gromacs.org/current/reference-manual/preface.html",
        }
    ),
    "lammps-cpu": frozenset(
        {
            "https://docs.lammps.org/Install.html",
            "https://docs.lammps.org/Build_prerequisites.html",
            "https://docs.lammps.org/Intro_opensource.html",
        }
    ),
    "gpumd-cuda": frozenset(
        {
            "https://github.com/brucefan1983/GPUMD/releases/latest",
            "https://gpumd.org/installation.html",
        }
    ),
    "gpumd-rocm": frozenset(
        {
            "https://github.com/brucefan1983/GPUMD/releases/latest",
            "https://gpumd.org/installation.html",
        }
    ),
    "lasp-commercial": frozenset(
        {
            "https://www.lasphub.com/",
            "https://pubs.acs.org/doi/10.1021/prechem.4c00060",
        }
    ),
    "deepmd-cpu-macos": frozenset(
        {
            "https://github.com/deepmodeling/deepmd-kit/releases/latest",
            "https://docs.deepmodeling.com/projects/deepmd/en/latest/install/easy-install.html",
        }
    ),
    "mace-python": frozenset(
        {
            "https://pypi.org/project/mace-torch/",
            "https://github.com/ACEsuit/mace/releases/tag/v0.3.16",
            "https://mace-docs.readthedocs.io/en/latest/guide/installation.html",
        }
    ),
    "nequip-python": frozenset(
        {
            "https://github.com/mir-group/nequip/releases/latest",
            "https://nequip.readthedocs.io/en/latest/guide/getting-started/install.html",
            "https://nequip.readthedocs.io/en/latest/guide/getting-started/files.html",
        }
    ),
    "fairchem-v1-gemnet-oc": frozenset(
        {
            "https://pypi.org/project/fairchem-core/1.10.0/",
            "https://fair-chem.github.io/fairchemv1-v2/",
            "https://fair-chem.github.io/models-1/",
        }
    ),
    "fairchem-v1-equiformer-v2": frozenset(
        {
            "https://pypi.org/project/fairchem-core/1.10.0/",
            "https://fair-chem.github.io/fairchemv1-v2/",
            "https://fair-chem.github.io/models-1/",
        }
    ),
    "fairchem-v2-uma": frozenset(
        {
            "https://pypi.org/project/fairchem-core/2.21.0/",
            "https://fair-chem.github.io/fairchemv1-v2/",
            "https://github.com/facebookresearch/fairchem",
        }
    ),
}
RESTRICTED_PROVIDER_IDS = frozenset(
    {"gaussian-g16-c02", "lasp-commercial", "lobster-5", "ovito-pro"}
)
ATTESTATION_FIELDS = {
    "attestation_id",
    "issued_on",
    "provider_id",
    "software_version",
    "user_authorized",
    "legal_use_confirmed",
    "installation_scope",
    "verification_method",
    "authorization_evidence_sha256",
    "binary_sha256",
    "capability_evidence_sha256",
    "binary_redistribution",
    "manual_redistribution",
    "fixture_redistribution",
    "attestation_sha256",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path() -> Path:
    return repo_root() / "registry" / "environment-profiles.yaml"


YamlLoader = Callable[[Path], object]


def load_registry(
    path: Path | None = None,
    *,
    yaml_loader: YamlLoader | None = None,
) -> dict[str, Any]:
    """Load the registry through an injectable path-based YAML loader.

    ``yaml_loader`` remains an intentionally narrow test and integration seam;
    production loading defaults to the shared duplicate-key-safe loader.
    """
    selected = path or registry_path()
    value = (yaml_loader or load_yaml_strict)(selected)
    if not isinstance(value, dict):
        raise RegistryYAMLError(
            "YAML_ROOT_NOT_MAPPING",
            selected.name,
            "document root must be a mapping",
        )
    return value


def _nonempty_strings(value: object, location: str, failures: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        failures.append(f"{location}: expected a nonempty list")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{location}/{index}: expected a nonempty string")
        else:
            result.append(item)
    return result


def _exact_fields(value: object, expected: set[str], location: str, failures: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        failures.append(f"{location}: expected a mapping")
        return {}
    if set(value) != expected:
        failures.append(
            f"{location}: expected fields {sorted(expected)}, found {sorted(map(str, value))}"
        )
    return value


def _required_and_optional_fields(
    value: object,
    required: set[str],
    optional: set[str],
    location: str,
    failures: list[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        failures.append(f"{location}: expected a mapping")
        return {}
    missing = required - set(value)
    extra = set(value) - required - optional
    if missing or extra:
        failures.append(
            f"{location}: missing fields {sorted(missing)}, unsupported fields {sorted(map(str, extra))}"
        )
    return value


def _date_is_valid(value: object, *, allow_unknown: bool = False) -> bool:
    if allow_unknown and value == "unknown":
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _python_version(value: object) -> tuple[int, ...] | None:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        return None
    return tuple(int(part) for part in value.split("."))


def _compare_version(value: tuple[int, ...], bound: tuple[int, ...]) -> int:
    width = max(len(value), len(bound))
    lhs = value + (0,) * (width - len(value))
    rhs = bound + (0,) * (width - len(bound))
    return (lhs > rhs) - (lhs < rhs)


def attestation_digest(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "attestation_sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_authorization(
    profile: dict[str, Any],
    *,
    category: object,
    provider_id: object,
    software_version: object,
    snapshot_date: object,
    location: str,
    failures: list[str],
) -> None:
    authorization = profile.get("authorization")
    if category != "restricted-proprietary":
        if "authorization" in profile:
            failures.append(
                f"{location}/authorization: only restricted providers may carry an external-trust receipt"
            )
        return
    authorization_data = _exact_fields(
        authorization,
        {"required", "provenance", "receipt"},
        f"{location}/authorization",
        failures,
    )
    if authorization_data.get("required") is not True:
        failures.append(f"{location}/authorization/required: restricted providers require authorization")
    if authorization_data.get("provenance") != "declared-requires-external-trust":
        failures.append(
            f"{location}/authorization/provenance: must be 'declared-requires-external-trust'"
        )
    record_value = authorization_data.get("receipt")
    if record_value is None:
        return

    receipt_location = f"{location}/authorization/receipt"
    record = _exact_fields(record_value, ATTESTATION_FIELDS, receipt_location, failures)
    if not record:
        return
    attestation_id = record.get("attestation_id")
    if not isinstance(attestation_id, str) or not ATTESTATION_ID.fullmatch(attestation_id):
        failures.append(f"{receipt_location}/attestation_id: invalid opaque identifier")
    elif isinstance(provider_id, str) and not attestation_id.startswith(f"att-{provider_id}-"):
        failures.append(f"{receipt_location}/attestation_id: identifier must bind the provider")
    if record.get("issued_on") != snapshot_date or not _date_is_valid(record.get("issued_on")):
        failures.append(f"{receipt_location}/issued_on: must equal the fixed snapshot date")
    if record.get("provider_id") != provider_id:
        failures.append(f"{receipt_location}/provider_id: provider identity must match")
    if record.get("software_version") != software_version:
        failures.append(f"{receipt_location}/software_version: software version must match")
    if record.get("user_authorized") is not True:
        failures.append(f"{receipt_location}/user_authorized: declaration must be true")
    if record.get("legal_use_confirmed") is not True:
        failures.append(f"{receipt_location}/legal_use_confirmed: declaration must be true")
    if record.get("installation_scope") != "runtime-local":
        failures.append(f"{receipt_location}/installation_scope: must be 'runtime-local'")
    if record.get("verification_method") != "user-authorized-hash-bound":
        failures.append(f"{receipt_location}/verification_method: unsupported verification method")
    digest_fields = (
        "authorization_evidence_sha256",
        "binary_sha256",
        "capability_evidence_sha256",
        "attestation_sha256",
    )
    for field in digest_fields:
        digest = record.get(field)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            failures.append(f"{receipt_location}/{field}: expected SHA-256")
    evidence_digests = [record.get(field) for field in digest_fields[:3]]
    if all(isinstance(item, str) and SHA256.fullmatch(item) for item in evidence_digests):
        if len(set(evidence_digests)) != len(evidence_digests):
            failures.append(f"{receipt_location}: evidence digests must be distinct")
    for field in ("binary_redistribution", "manual_redistribution", "fixture_redistribution"):
        if record.get(field) is not False:
            failures.append(f"{receipt_location}: redistribution flags must all be false")
            break
    try:
        expected_digest = attestation_digest(record)
    except (TypeError, ValueError):
        failures.append(f"{receipt_location}: receipt cannot be canonically hashed")
    else:
        if record.get("attestation_sha256") != expected_digest:
            failures.append(f"{receipt_location}: receipt digest mismatch")


def _current_python_supported(python: dict[str, Any]) -> bool:
    if not python.get("required"):
        return True
    lower = _python_version(python.get("min_inclusive"))
    upper = _python_version(python.get("max_exclusive"))
    if lower is None:
        return False
    if _compare_version(CURRENT_PYTHON, lower) < 0:
        return False
    return upper is None or _compare_version(CURRENT_PYTHON, upper) < 0


def _target_support(targets: object) -> tuple[bool, bool]:
    platform_supported = False
    architecture_supported = False
    if not isinstance(targets, list):
        return platform_supported, architecture_supported
    for target in targets:
        if not isinstance(target, dict):
            continue
        if target.get("platform") == CURRENT_PLATFORM:
            platform_supported = True
            architectures = target.get("architectures")
            if isinstance(architectures, list) and CURRENT_ARCHITECTURE in architectures:
                architecture_supported = True
    return platform_supported, architecture_supported


def _validate_url(url: object, location: str, failures: list[str]) -> None:
    if not isinstance(url, str) or not url.strip():
        failures.append(f"{location}: expected a nonempty URL")
        return
    parsed = urlsplit(url)
    domain = (parsed.hostname or "").lower()
    if parsed.username or parsed.password:
        failures.append(f"{location}: URL user information is forbidden")
    if parsed.fragment:
        failures.append(f"{location}: URL fragments are forbidden")
    if domain not in OFFICIAL_DOMAINS:
        failures.append(f"{location}: non-official URL domain {domain!r}")
    if parsed.scheme == "http" and domain not in LEGACY_HTTP_DOMAINS:
        failures.append(f"{location}: HTTPS is required for {domain!r}")
    elif parsed.scheme not in {"http", "https"}:
        failures.append(f"{location}: expected an HTTP(S) URL")


def _sensitive_errors(value: object, location: str = "<root>") -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            child = f"{location}/{key_text}"
            if FORBIDDEN_KEY.search(key_text):
                yield f"{child}: sensitive identity or location field is forbidden"
            yield from _sensitive_errors(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _sensitive_errors(item, f"{location}/{index}")
    elif isinstance(value, str) and not value.startswith(("http://", "https://")):
        if LOCAL_LOCATION.search(value):
            yield f"{location}: real local filesystem location is forbidden"
        if REMOTE_IDENTITY.search(value):
            yield f"{location}: remote identity or endpoint is forbidden"
        if SECRET_ASSIGNMENT.search(value):
            yield f"{location}: sensitive assignment is forbidden"


def validation_errors(data: object) -> list[str]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    expected_root = {"schema_version", "as_of", "snapshot", "profiles"}
    if set(data) != expected_root:
        failures.append(
            f"<root>: expected fields {sorted(expected_root)}, found {sorted(map(str, data))}"
        )
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version: expected {SCHEMA_VERSION!r}")
    if not _date_is_valid(data.get("as_of")):
        failures.append("as_of: expected an ISO YYYY-MM-DD date")
    snapshot = _exact_fields(
        data.get("snapshot"),
        {"kind", "observed_on", "machine_class", "dynamic_detection"},
        "snapshot",
        failures,
    )
    if snapshot.get("kind") != "fixed-current-machine-observation":
        failures.append("snapshot/kind: expected a fixed current-machine observation")
    if snapshot.get("observed_on") != CURRENT_SNAPSHOT_DATE:
        failures.append(f"snapshot/observed_on: expected {CURRENT_SNAPSHOT_DATE!r}")
    if data.get("as_of") != snapshot.get("observed_on"):
        failures.append("snapshot/observed_on: must equal as_of")
    if snapshot.get("machine_class") != CURRENT_MACHINE_CLASS:
        failures.append(f"snapshot/machine_class: expected {CURRENT_MACHINE_CLASS!r}")
    if snapshot.get("dynamic_detection") is not False:
        failures.append("snapshot/dynamic_detection: profiles are a fixed snapshot, not CI dynamic detection")

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        failures.append("profiles: expected a nonempty mapping")
        profiles = {}
    for provider_id in profiles:
        if provider_id not in REVIEWED_PROVIDER_URLS:
            failures.append(
                f"profiles/{provider_id}/official_urls: provider has no reviewed URL authority mapping"
            )
    for provider_id in sorted(REVIEWED_PROVIDER_URLS):
        if provider_id not in profiles:
            failures.append(
                f"profiles/{provider_id}: reviewed URL authority provider is missing from the registry"
            )

    expected_profile = {
        "provider_id",
        "profile_type",
        "role",
        "source_tier",
        "software",
        "official_urls",
        "license",
        "environment",
        "assets",
        "runtime_probe",
        "known_exclusions",
        "current_machine",
        "planned_blockers",
        "maximum_validation_level",
    }
    seen_provider_ids: set[str] = set()
    for key, raw_profile in profiles.items():
        location = f"profiles/{key}"
        if not isinstance(key, str) or not PROFILE_ID.fullmatch(key):
            failures.append(f"{location}: invalid profile identifier")
        profile = _required_and_optional_fields(raw_profile, expected_profile, {"authorization"}, location, failures)
        if not profile:
            continue

        provider_id = profile.get("provider_id")
        if provider_id != key:
            failures.append(f"{location}/provider_id: must equal mapping key {key!r}")
        if not isinstance(provider_id, str) or not PROFILE_ID.fullmatch(provider_id):
            failures.append(f"{location}/provider_id: invalid provider identifier")
        elif provider_id in seen_provider_ids:
            failures.append(f"{location}/provider_id: duplicate provider identifier")
        else:
            seen_provider_ids.add(provider_id)

        profile_type = profile.get("profile_type")
        role = profile.get("role")
        if profile_type not in PROFILE_TYPES:
            failures.append(f"{location}/profile_type: unsupported value {profile_type!r}")
        if role not in ROLES:
            failures.append(f"{location}/role: unsupported value {role!r}")
        elif profile_type in PROFILE_ROLE_COMPATIBILITY and role not in PROFILE_ROLE_COMPATIBILITY[profile_type]:
            failures.append(f"{location}: profile_type {profile_type!r} is incompatible with role {role!r}")
        source_tier = profile.get("source_tier")
        if source_tier not in SOURCE_TIERS:
            failures.append(f"{location}/source_tier: unsupported value {source_tier!r}")

        software = _exact_fields(
            profile.get("software"), {"name", "version", "release_date"}, f"{location}/software", failures
        )
        for field in ("name", "version"):
            if not isinstance(software.get(field), str) or not software.get(field, "").strip():
                failures.append(f"{location}/software/{field}: expected a nonempty string")
        release_date = software.get("release_date")
        if not _date_is_valid(release_date, allow_unknown=True):
            failures.append(f"{location}/software/release_date: expected ISO date or 'unknown'")

        urls = profile.get("official_urls")
        if not isinstance(urls, list) or not urls:
            failures.append(f"{location}/official_urls: expected a nonempty list")
        else:
            if len(urls) != len(set(map(str, urls))):
                failures.append(f"{location}/official_urls: duplicate URLs are forbidden")
            for index, url in enumerate(urls):
                _validate_url(url, f"{location}/official_urls/{index}", failures)
            reviewed_urls = REVIEWED_PROVIDER_URLS.get(key)
            if (
                reviewed_urls is not None
                and all(isinstance(url, str) for url in urls)
                and frozenset(urls) != reviewed_urls
            ):
                failures.append(
                    f"{location}/official_urls: URL set differs from reviewed provider authority"
                )

        license_data = _exact_fields(
            profile.get("license"),
            {"category", "identifier", "redistribution", "obligations"},
            f"{location}/license",
            failures,
        )
        category = license_data.get("category")
        redistribution = license_data.get("redistribution")
        if category not in LICENSE_CATEGORIES:
            failures.append(f"{location}/license/category: unsupported value {category!r}")
        if key in RESTRICTED_PROVIDER_IDS and category != "restricted-proprietary":
            failures.append(
                f"{location}/license/category: reviewed restricted provider identity cannot be reclassified"
            )
        if category == "restricted-proprietary" and key not in RESTRICTED_PROVIDER_IDS:
            failures.append(
                f"{location}/license/category: provider lacks a reviewed restricted provider identity"
            )
        if not isinstance(license_data.get("identifier"), str) or not license_data.get("identifier", "").strip():
            failures.append(f"{location}/license/identifier: expected a nonempty string")
        if redistribution not in REDISTRIBUTION_VALUES:
            failures.append(f"{location}/license/redistribution: unsupported value {redistribution!r}")
        elif category in LICENSE_REDISTRIBUTION and redistribution not in LICENSE_REDISTRIBUTION[category]:
            failures.append(
                f"{location}/license: category {category!r} is incompatible with redistribution {redistribution!r}"
            )
        _nonempty_strings(license_data.get("obligations"), f"{location}/license/obligations", failures)
        _validate_authorization(
            profile,
            category=category,
            provider_id=provider_id,
            software_version=software.get("version"),
            snapshot_date=snapshot.get("observed_on"),
            location=location,
            failures=failures,
        )

        environment = _exact_fields(
            profile.get("environment"),
            {"targets", "python", "compiler", "mpi", "gpu"},
            f"{location}/environment",
            failures,
        )
        targets = environment.get("targets")
        if not isinstance(targets, list) or not targets:
            failures.append(f"{location}/environment/targets: expected a nonempty list")
            targets = []
        seen_platforms: set[str] = set()
        for index, raw_target in enumerate(targets):
            target_location = f"{location}/environment/targets/{index}"
            target = _exact_fields(raw_target, {"platform", "architectures"}, target_location, failures)
            platform = target.get("platform")
            if platform not in PLATFORMS:
                failures.append(f"{target_location}/platform: unsupported value {platform!r}")
            elif platform in seen_platforms:
                failures.append(f"{target_location}/platform: duplicate platform")
            else:
                seen_platforms.add(platform)
            architectures = target.get("architectures")
            if not isinstance(architectures, list) or not architectures:
                failures.append(f"{target_location}/architectures: expected a nonempty list")
            elif len(architectures) != len(set(map(str, architectures))):
                failures.append(f"{target_location}/architectures: duplicate values are forbidden")
            else:
                for architecture in architectures:
                    if architecture not in ARCHITECTURES:
                        failures.append(f"{target_location}/architectures: unsupported value {architecture!r}")

        python = _exact_fields(
            environment.get("python"),
            {"required", "min_inclusive", "max_exclusive"},
            f"{location}/environment/python",
            failures,
        )
        python_required = python.get("required")
        if not isinstance(python_required, bool):
            failures.append(f"{location}/environment/python/required: expected boolean")
        lower = _python_version(python.get("min_inclusive"))
        upper_value = python.get("max_exclusive")
        upper = _python_version(upper_value)
        if python_required:
            if lower is None:
                failures.append(f"{location}/environment/python/min_inclusive: expected X.Y or X.Y.Z")
            if upper_value is not None and upper is None:
                failures.append(f"{location}/environment/python/max_exclusive: expected null, X.Y, or X.Y.Z")
            if lower is not None and upper is not None and _compare_version(lower, upper) >= 0:
                failures.append(f"{location}/environment/python: minimum must be below maximum")
        elif python.get("min_inclusive") is not None or upper_value is not None:
            failures.append(f"{location}/environment/python: bounds require required=true")

        for component in ("compiler", "mpi"):
            specification = _exact_fields(
                environment.get(component),
                {"required", "requirements"},
                f"{location}/environment/{component}",
                failures,
            )
            if not isinstance(specification.get("required"), bool):
                failures.append(f"{location}/environment/{component}/required: expected boolean")
            requirements = specification.get("requirements")
            if not isinstance(requirements, list):
                failures.append(f"{location}/environment/{component}/requirements: expected a list")
            elif specification.get("required") and not requirements:
                failures.append(f"{location}/environment/{component}/requirements: required component needs details")
            else:
                for index, requirement in enumerate(requirements):
                    if not isinstance(requirement, str) or not requirement.strip():
                        failures.append(
                            f"{location}/environment/{component}/requirements/{index}: expected a nonempty string"
                        )

        gpu = _exact_fields(
            environment.get("gpu"), {"required", "backends"}, f"{location}/environment/gpu", failures
        )
        if not isinstance(gpu.get("required"), bool):
            failures.append(f"{location}/environment/gpu/required: expected boolean")
        backends = gpu.get("backends")
        if not isinstance(backends, list):
            failures.append(f"{location}/environment/gpu/backends: expected a list")
        else:
            for backend in backends:
                if backend not in GPU_BACKENDS:
                    failures.append(f"{location}/environment/gpu/backends: unsupported value {backend!r}")
            if gpu.get("required") and not backends:
                failures.append(f"{location}/environment/gpu/backends: required GPU needs a backend")

        assets = _exact_fields(
            profile.get("assets"), {"model_license", "data_license", "notes"}, f"{location}/assets", failures
        )
        for field in ("model_license", "data_license"):
            if assets.get(field) not in ASSET_LICENSE_VALUES:
                failures.append(f"{location}/assets/{field}: unsupported value {assets.get(field)!r}")
        _nonempty_strings(assets.get("notes"), f"{location}/assets/notes", failures)

        probe = _exact_fields(
            profile.get("runtime_probe"),
            {"kind", "target", "expected_identity", "execution_policy"},
            f"{location}/runtime_probe",
            failures,
        )
        if probe.get("kind") not in PROBE_KINDS:
            failures.append(f"{location}/runtime_probe/kind: unsupported value {probe.get('kind')!r}")
        for field in ("target", "expected_identity"):
            value = probe.get(field)
            if not isinstance(value, str) or not value.strip():
                failures.append(f"{location}/runtime_probe/{field}: expected a nonempty string")
            elif any(operator in value for operator in (";", "&&", "||", "`", "$(", "\n")):
                failures.append(f"{location}/runtime_probe/{field}: shell operators are forbidden")
        if probe.get("execution_policy") != "documentary-read-only":
            failures.append(
                f"{location}/runtime_probe/execution_policy: must be 'documentary-read-only'"
            )

        known_exclusions = _nonempty_strings(
            profile.get("known_exclusions"), f"{location}/known_exclusions", failures
        )
        blockers = _nonempty_strings(profile.get("planned_blockers"), f"{location}/planned_blockers", failures)
        if release_date == "unknown" and not any("release date" in item.lower() for item in known_exclusions):
            failures.append(f"{location}/known_exclusions: unknown release date must be explicit")

        current = _exact_fields(
            profile.get("current_machine"), {"status", "observations"}, f"{location}/current_machine", failures
        )
        status = current.get("status")
        if status not in CURRENT_STATUSES:
            failures.append(f"{location}/current_machine/status: unsupported value {status!r}")
        _nonempty_strings(current.get("observations"), f"{location}/current_machine/observations", failures)

        maximum = profile.get("maximum_validation_level")
        if maximum not in VALIDATION_LEVELS:
            failures.append(f"{location}/maximum_validation_level: unsupported value {maximum!r}")
        platform_supported, architecture_supported = _target_support(targets)
        if status == "unsupported-platform" and platform_supported:
            failures.append(f"{location}/current_machine: status conflicts with supported macOS target")
        if status == "unsupported-architecture" and (not platform_supported or architecture_supported):
            failures.append(f"{location}/current_machine: architecture status conflicts with targets")
        if status == "unsupported-runtime" and _current_python_supported(python):
            failures.append(f"{location}/current_machine: runtime status conflicts with Python bounds")
        if status in {"installed-compatible", "not-installed-compatible", "restricted-installed"}:
            if not platform_supported or not architecture_supported or not _current_python_supported(python):
                failures.append(f"{location}/current_machine: compatible status conflicts with environment")
        if status == "unsupported-hardware" and (not gpu.get("required") or "metal" in (backends or [])):
            failures.append(f"{location}/current_machine: hardware status requires a non-Metal mandatory GPU")
        if status == "restricted-unavailable" and category != "restricted-proprietary":
            failures.append(f"{location}/current_machine: restricted status requires restricted-proprietary license")
        if status == "restricted-installed" and category != "restricted-proprietary":
            failures.append(f"{location}/current_machine: restricted-installed requires restricted-proprietary license")
        installed_statuses = {"installed-compatible", "restricted-installed"}
        if status in installed_statuses and maximum == "planned":
            failures.append(f"{location}/maximum_validation_level: installed status must allow environment verification")
        if status not in installed_statuses and maximum != "planned":
            failures.append(f"{location}/maximum_validation_level: unavailable profile must remain planned")

        if category == "restricted-proprietary":
            if redistribution != "prohibited":
                failures.append(f"{location}/license: restricted redistribution must be prohibited")
            if status != "restricted-unavailable":
                failures.append(
                    f"{location}/current_machine: provider requires external trust and must remain restricted-unavailable"
                )
            if maximum != "planned":
                failures.append(
                    f"{location}/maximum_validation_level: provider requires external trust and must remain planned"
                )
            if not any("external trust" in blocker.lower() for blocker in blockers):
                failures.append(
                    f"{location}/planned_blockers: restricted provider requires an external trust blocker"
                )
        if source_tier == "third-party-community-referenced-by-official":
            if maximum != "planned" or status != "unverified":
                failures.append(f"{location}: community provider must remain unverified and planned")
            if not any("first-party" in blocker.lower() for blocker in blockers):
                failures.append(f"{location}/planned_blockers: community provider needs a first-party evidence blocker")

    failures.extend(_sensitive_errors(data))
    return failures


def machine_summary(data: dict[str, Any]) -> dict[str, Any]:
    """Summarize the validated fixed snapshot without implying software execution."""
    profiles = data["profiles"]
    requires_external_trust = sorted(RESTRICTED_PROVIDER_IDS.intersection(profiles))
    status_counts: dict[str, int] = {}
    for profile in profiles.values():
        status = profile["current_machine"]["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    maximum_level = max(
        (profile["maximum_validation_level"] for profile in profiles.values()),
        key=VALIDATION_LEVELS.index,
    )
    return {
        "registry_valid": True,
        "dynamic_detection": data["snapshot"]["dynamic_detection"],
        "software_executed": False,
        "external_trust_resolver_configured": False,
        "requires_external_trust": requires_external_trust,
        "profile_count": len(profiles),
        "current_status_counts": dict(sorted(status_counts.items())),
        "maximum_current_machine_validation_level": maximum_level,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=registry_path())
    args = parser.parse_args(argv)
    try:
        data = load_registry(args.registry)
    except RegistryYAMLError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    failures = validation_errors(data)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 2
    print(json.dumps(machine_summary(data), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
