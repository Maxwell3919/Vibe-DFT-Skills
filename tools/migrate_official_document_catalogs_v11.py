#!/usr/bin/env python3
"""Pure v1.0 to v1.1 official-document-source-catalog converter.

The converter is deterministic, side-effect free, and projection-only. It only
transforms already-parsed records and does not enumerate files, write seeds,
resolve network resources, or build packs.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any


SCHEMA_VERSION = "1.1"
CONTRACT_NAME = "official-document-source-catalog"
VERSION_SCOPE_KINDS = {
    "exact",
    "revision",
    "release-line",
    "latest-at-retrieval",
    "unversioned",
}

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
HTTPS_URL_RE = re.compile(r"^https://")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

SELECTOR_LAYER_FIXES = {"raw-source"}

LIMITATION_CLEAN_TEXT = "Selector kind json-pointer is retained; no virtual selector body bytes are introduced by migration."
MIGRATION_INVENTORY_LIMITATION = (
    "The inventory identity binds the exact pre-migration catalog bytes as "
    "migration metadata; it does not identify any upstream document body."
)


@dataclass(frozen=True)
class LegacyRecordAction:
    """One reviewed, exact, one-time v1.0 migration action.

    The ledger deliberately has no keyword or policy classifier. A record is
    actionable only when its provider input, typed identity, and canonical
    record hash are the reviewed values below.
    """

    record_type: str
    provider_input_id: str
    record_id: str
    expected_sha256: str | None
    action: str
    replacement_id: str | None = None
    replacement_text: str | None = None
    expected_scope_statement: str | None = None
    replacement_statement: str | None = None


def _legacy_action(
    record_type: str,
    provider_input_id: str,
    record_id: str,
    expected_sha256: str | None,
    action: str,
    *,
    replacement_id: str | None = None,
    replacement_text: str | None = None,
    expected_scope_statement: str | None = None,
    replacement_statement: str | None = None,
) -> LegacyRecordAction:
    return LegacyRecordAction(
        record_type=record_type,
        provider_input_id=provider_input_id,
        record_id=record_id,
        expected_sha256=expected_sha256,
        action=action,
        replacement_id=replacement_id,
        replacement_text=replacement_text,
        expected_scope_statement=expected_scope_statement,
        replacement_statement=replacement_statement,
    )


# Exact reviewed ledger: blocker=10, loss=10, subject occurrences=26,
# limitation=12, exclusion rationale=2. The actions are conversion-only and do
# not become a production/runtime judgment mechanism.
LEGACY_RECORD_ACTIONS: tuple[LegacyRecordAction, ...] = (
    # Blockers: drop=5, rename=4, rewrite=1.
    _legacy_action(
        "blocker", "gpumd-docs", "MODEL.DATA.LICENSE.IDENTITY.MISSING",
        "e68a42dcfea64fb6d8165c14acd0ca88e568d127fe784d560085ba7414f798a9",
        "rename",
        replacement_id="MODEL.DATA.IDENTITY.MISSING",
        replacement_text=(
            "Potential/model files, datasets, trained weights, and executable "
            "examples require independent byte identities and provenance records."
        ),
    ),
    _legacy_action(
        "blocker", "mace-docs", "MACE_DOCS_LICENSE_CONDITIONAL",
        "4737f60a3543f802fd6288ef8a118ebdbba5bb063d99be64cfd6ea9c0ac19850",
        "drop",
    ),
    _legacy_action(
        "blocker", "mace-docs", "MACE_MODEL_LICENSES_SPLIT",
        "12167b5edc31bd93d9b785f4b787b764dcc7ed50ab8ea13bf514b06db246df28",
        "rename",
        replacement_id="MACE_MODEL_IDENTITIES_SPLIT",
        replacement_text=(
            "Foundation-model families have separate artifact identities, and no "
            "selected model artifact identity is established here."
        ),
    ),
    _legacy_action(
        "blocker", "fairchem-v1", "FAIRCHEM_V1_WEIGHTS_LICENSE_UNKNOWN",
        "796f193319a969fc658ff2a5cf586acea60182d00ebe7b02518d9eb0ab0f42fe",
        "rename",
        replacement_id="FAIRCHEM_V1_WEIGHTS_IDENTITY_MISSING",
        replacement_text="Byte identities for legacy checkpoints are unresolved.",
    ),
    _legacy_action(
        "blocker", "uma-models", "UMA_MODEL_TERMS_REVIEW_REQUIRED",
        "e5a8b996ad70b8928c7f9c802c86159b4e6e03b01b91d9495b7cbe3e5442798f",
        "drop",
    ),
    _legacy_action(
        "blocker", "fairchem-datasets",
        "FAIRCHEM_REFERENCE_DFT_RIGHTS_UNRESOLVED",
        "7fe8a7599ba1de03815a0b5b9247146ec2c0a38caab821ec33dd66c17dcf4263",
        "rename",
        replacement_id="FAIRCHEM_REFERENCE_DFT_PROVENANCE_UNRESOLVED",
        replacement_text=(
            "Reference software, potential, raw-output, and gated-storage "
            "identities and provenance remain independent and unresolved."
        ),
    ),
    _legacy_action(
        "blocker", "multiwfn-manual", "LICENSE.DERIVATIVE.RIGHTS.UNRESOLVED",
        "ba760688a5e32f3777bec427ad4d6b1778e0cb20e34a3526c355ec2f8840ddad",
        "drop",
    ),
    _legacy_action(
        "blocker", "ovito-docs", "LICENSE.COMPONENT.ARTIFACT.CLOSURE.MISSING",
        "e564cc5fe0cdd5452ea2c08d8443443a083e50b6a595f5c1075ec9bc05c43dfb",
        "drop",
    ),
    _legacy_action(
        "blocker", "vaspkit-docs", "LICENSE.DOCUMENTATION.RIGHTS.UNRESOLVED",
        "e3049bc74eab90384ff31b85cf7c2ff13f6f7322ee607e9eb8c801643025f91e",
        "drop",
    ),
    _legacy_action(
        "blocker", "vaspkit-docs", "RUNTIME.BINARY.PARENT.CLOSURE.MISSING",
        "808da5a959e3fe7400d0cc80a3912acf7b6260bb92372ec2d4d8813bbd2ee6d4",
        "rewrite",
        replacement_text=(
            "Exact binary/menu/help, configuration, POTCAR, and accepted parent "
            "VASP evidence are not covered by the docs authority."
        ),
    ),
    # Losses: drop=2, rename=1, preserve=1, rewrite=6.
    _legacy_action(
        "loss", "mace-framework", "mace-framework-bodies-external",
        "51e85a2f99a967da1cfd4200b47faad39c9a2be5de15f05703c646ca5402cfac",
        "preserve",
    ),
    _legacy_action(
        "loss", "mace-docs", "mace-docs-bodies-external",
        "39cb3192db6aa11c41d487c88e68ae0cabf305eb9fb0e72204acb08f949f2438",
        "rewrite",
        replacement_text=(
            "The docs tree, rendered index, guide, and branch metadata bodies "
            "remain external; only exact receipts are tracked."
        ),
    ),
    _legacy_action(
        "loss", "nequip-framework", "nequip-bodies-external",
        "19dd334b938fbf28639a31d5bebc5024e17160ee89f99ebb7351b5439342d63b",
        "rewrite",
        replacement_text=(
            "Exact docs, code, and repository metadata bodies are represented "
            "only by external git-object receipts."
        ),
    ),
    _legacy_action(
        "loss", "fairchem-v1", "fairchem-v1-bodies-external",
        "d9adee8f5d15c11a56784b4fe2dd9b68966b99273ac95e6fa661afa4a510b8cb",
        "rewrite",
        replacement_text="Exact v1 docs, source, and repository metadata bodies remain external.",
    ),
    _legacy_action(
        "loss", "fairchem-v2", "fairchem-v2-bodies-external",
        "e8646d305467a7757e357aca4d9b6257312b95e4b0a3170846fcbeb984120d28",
        "rewrite",
        replacement_text="Exact v2 docs, source, and repository metadata bodies remain external.",
    ),
    _legacy_action(
        "loss", "fairchem-datasets", "fairchem-dataset-doc-bodies-external",
        "21898e8cb7c2d5cca0c05f8e058db5a53b55bd502cbd1e3d6df03e22a0b2c19a",
        "rewrite",
        replacement_text=(
            "Exact dataset and UMA documentation bodies remain external; only "
            "byte receipts and technical provenance subjects are stored."
        ),
    ),
    _legacy_action(
        "loss", "fairchem-datasets",
        "fairchem-external-dataset-artifact-revisions",
        "149e9461597d7ae09d7dac95137014ab4defff3a449f53cfefb10b4a7b7deb59",
        "rewrite",
        replacement_text=(
            "Documentation revision does not establish each external dataset "
            "archive's byte identity or storage revision."
        ),
    ),
    _legacy_action(
        "loss", "multiwfn-manual",
        "custom-license-derivative-rights-unresolved",
        "1156ff1d7c635b39b92a2f0b11ce37bf288aa7973eeb43a672a59fde575ba576",
        "drop",
    ),
    _legacy_action(
        "loss", "ovito-docs",
        "third-party-and-artifact-license-closure-external",
        "664e672a906d48831dc9ad782f97013c008014559e29167fac4fe25a6f67d49f",
        "rename",
        replacement_id="third-party-and-artifact-provenance-closure-external",
        replacement_text=(
            "Third-party notices, distribution artifacts, Pro binaries, user "
            "trajectories, and generated artifacts require separate identity and "
            "provenance closure."
        ),
    ),
    _legacy_action(
        "loss", "vaspkit-docs", "documentation-license-unresolved",
        "ffa8c2a2e384c4c621c80d1d9e7b8e86fd4a7f39b488b46be618c2c83ffd1fae",
        "drop",
    ),
    # Subjects: drop=5, rename=21. Repeated subject IDs are intentionally
    # separate provider-input occurrences.
    _legacy_action(
        "subject", "gaussian-g16-c01-public", "g16-licensed-runtime",
        "ebc54e80b28c8e0b355c2a78c7a67e814a39c83850e85f49ac1dbe7c76bbb257",
        "drop",
        expected_scope_statement=(
            "A public reference cannot establish a licensed executable, private "
            "manual, checkpoint, basis payload, or execution authorization."
        ),
    ),
    _legacy_action(
        "subject", "gaussian-g16-c02-delta", "g16-licensed-runtime",
        "ebc54e80b28c8e0b355c2a78c7a67e814a39c83850e85f49ac1dbe7c76bbb257",
        "drop",
        expected_scope_statement=(
            "A public reference cannot establish a licensed executable, private "
            "manual, checkpoint, basis payload, or execution authorization."
        ),
    ),
    _legacy_action(
        "subject", "gpumd-docs", "license.execution-boundary",
        "25f26dfbf10cefa85e21b4fcd9e95ed9b1356a9eae491127dcd2410387e907af",
        "rename",
        replacement_id="execution.provenance-boundary",
        replacement_text=(
            "Source, model/data, GPU runtime, privacy, and execution provenance "
            "boundaries"
        ),
        expected_scope_statement=(
            "Source licensing, external model/data licensing, GPU runtime terms, "
            "privacy, and execution authorization are separate boundaries."
        ),
        replacement_statement=(
            "Source revision, external model/data identity, GPU runtime identity, "
            "privacy, and execution authorization are separate technical boundaries."
        ),
    ),
    _legacy_action(
        "subject", "lasp-author-literature", "lasp-3-7-3-license-terms",
        "7aeaa69572a6992e06bddcb6ec0b7b0a3ac9397adfe257d8e23ee17c215ca64c",
        "drop",
        expected_scope_statement=(
            "Complete LASP software, manual, examples, model, interface, and "
            "redistribution terms are not established by the HTTPS literature."
        ),
    ),
    _legacy_action(
        "subject", "lobster-acs-method-literature",
        "lobster-5-1-1-license-boundary",
        "0a6d8548cc90448418f62c8596e80855fdfd4b9104481b2829e2327ff8b8f773",
        "drop",
        expected_scope_statement=(
            "The registered non-profit license and non-redistribution boundary is "
            "reported by a query-bearing first-party page that cannot be activated "
            "under the central query policy; external entitlement evidence remains "
            "required and bundled payloads remain prohibited."
        ),
    ),
    _legacy_action(
        "subject", "lobster-wiley-method-literature",
        "lobster-5-1-1-license-boundary",
        "0a6d8548cc90448418f62c8596e80855fdfd4b9104481b2829e2327ff8b8f773",
        "drop",
        expected_scope_statement=(
            "The registered non-profit license and non-redistribution boundary is "
            "reported by a query-bearing first-party page that cannot be activated "
            "under the central query policy; external entitlement evidence remains "
            "required and bundled payloads remain prohibited."
        ),
    ),
    _legacy_action(
        "subject", "mace-framework", "mace.framework.license",
        "4d09b4023164fcbf8cf32de68a3c9f530e5ffde6c29390d1bda97e5732df5051",
        "rename",
        replacement_id="mace.framework.artifact-identity",
        replacement_text="MACE framework revision and artifact identity boundary",
        expected_scope_statement=(
            "The v0.3.16 framework LICENSE is MIT and applies to that source "
            "release only; it does not license the separate docs branch, model "
            "artifacts, datasets, or reference-DFT artifacts."
        ),
        replacement_statement=(
            "The v0.3.16 framework source revision does not establish the distinct "
            "docs branch, model, dataset, or reference-DFT artifact identities."
        ),
    ),
    _legacy_action(
        "subject", "mace-docs", "mace.docs.license",
        "95577838e06e555e45a6eb00b06a36287470133453f92656be0f28c3ab051962",
        "rename",
        replacement_id="mace.docs.branch-identity",
        replacement_text="MACE docs branch identity boundary",
        expected_scope_statement=(
            "The reviewed docs branch LICENSE is an Academic Software License with "
            "academic/noncommercial restrictions and is not the framework release "
            "MIT license."
        ),
        replacement_statement=(
            "The reviewed docs branch and framework release are distinct repository "
            "revisions with independent source identities."
        ),
    ),
    _legacy_action(
        "subject", "mace-docs", "mace.docs.model.license.split",
        "c5c4da210d306ec63cf53e38baccdae29a043a0dd4fa3368adee79f5fd667856",
        "rename",
        replacement_id="mace.docs.model.identity.split",
        replacement_text="MACE model-artifact identity split",
        expected_scope_statement=(
            "The foundation-model page records different licenses across model "
            "families; a framework or docs license never establishes a selected "
            "model artifact's license."
        ),
        replacement_statement=(
            "The foundation-model page records distinct model families; a framework "
            "or docs revision does not establish any selected model artifact's byte "
            "identity."
        ),
    ),
    _legacy_action(
        "subject", "nequip-framework", "nequip.framework.license.boundary",
        "c929939dc8543b84244c1d8fa6728d80314409833ac95d8d0ed2156a376b77cc",
        "rename",
        replacement_id="nequip.framework.artifact-identity.boundary",
        replacement_text="NequIP framework/checkpoint/data identity split",
        expected_scope_statement=(
            "The v0.19.0 source license is MIT; checkpoints, packaged models and "
            "training data require separate identities and license evidence."
        ),
        replacement_statement=(
            "The v0.19.0 source revision, checkpoints, packaged models, and training "
            "data require separate artifact identities and provenance records."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-v1", "fairchem.v1.framework.license",
        "58bebf53f8e20df9b23b1a47ba46e6f607fb0f8db3bdaf8e35e82f2e9da9d63c",
        "rename",
        replacement_id="fairchem.v1.framework.identity",
        replacement_text="FairChem v1 framework source identity",
        expected_scope_statement=(
            "The reviewed repository source is MIT; this does not establish any "
            "legacy pretrained checkpoint license."
        ),
        replacement_statement=(
            "The reviewed repository source revision does not establish any legacy "
            "pretrained checkpoint byte identity."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-v1", "fairchem.v1.weights.license.unknown",
        "bab493ce9cbe153a02dfc2b71319169fbbee31117e35f0d7a1c66aa736b495da",
        "rename",
        replacement_id="fairchem.v1.weights.identity.unknown",
        replacement_text="FairChem v1 legacy checkpoint identity gap",
        expected_scope_statement=(
            "Legacy model pages identify datasets and checkpoints but do not "
            "provide sufficient artifact-specific weight-license evidence; weights "
            "remain excluded and unresolved."
        ),
        replacement_statement=(
            "Legacy model pages identify datasets and checkpoints but do not provide "
            "the selected checkpoint byte identities; weights remain excluded."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-v2", "fairchem.v2.framework.license",
        "f56fbd86a61f8a86ade2a50cb7e0ad99eb53bdcd6f3d3a29a4a76eddd1fe03c7",
        "rename",
        replacement_id="fairchem.v2.framework.identity",
        replacement_text="FairChem v2 framework source identity",
        expected_scope_statement=(
            "The reviewed repository source is MIT; the UMA model repository, "
            "pretrained weights, datasets and reference-DFT artifacts have separate "
            "rights records."
        ),
        replacement_statement=(
            "The reviewed repository source, UMA model repository, pretrained "
            "weights, datasets, and reference-DFT artifacts require separate "
            "identity and provenance records."
        ),
    ),
    _legacy_action(
        "subject", "uma-models", "uma.model.license.restricted",
        "96330e1eb8fecd736539b8be8fea98420a1f826b593ab393a80979ecc309aa3b",
        "rename",
        replacement_id="uma.model.artifact.gated",
        replacement_text="UMA gated model-artifact boundary",
        expected_scope_statement=(
            "The public repository metadata reports license:other and gated FAIR "
            "Chemistry License v1 plus Acceptable Use Policy terms; the FairChem "
            "framework MIT license does not apply to UMA weights."
        ),
        replacement_statement=(
            "The public repository metadata reports a gated model repository; the "
            "FairChem framework source identity does not establish UMA weight bytes."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.omol25.license-protocol",
        "437ed9f1b6dc9693c1eb74e298340f6d5d59e06a2e776734c2733dded1dab293",
        "rename",
        replacement_id="fairchem.dataset.omol25.reference-protocol",
        replacement_text="OMol25 reference protocol",
        expected_scope_statement=(
            "The exact OMol25 page states CC-BY-4.0 dataset terms and ORCA 6 "
            "reference calculations using wB97M-V/def2-TZVPD; this does not grant "
            "ORCA software or raw-output redistribution rights."
        ),
        replacement_statement=(
            "The exact OMol25 page records ORCA 6 reference calculations using "
            "wB97M-V/def2-TZVPD; software and raw-output identities remain separate."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.omc25.license-protocol",
        "4f1a79cb5bfddb33ce8da2b4908c58dccd0675fcb35808fd303e8f1747e8a498",
        "rename",
        replacement_id="fairchem.dataset.omc25.reference-protocol",
        replacement_text="OMC25 reference protocol",
        expected_scope_statement=(
            "The exact OMC25 page states CC-BY-4.0 dataset terms and VASP PBE+D3 "
            "reference calculations; VASP and PAW/POTCAR rights remain separate."
        ),
        replacement_statement=(
            "The exact OMC25 page records VASP PBE+D3 reference calculations; VASP "
            "and PAW/POTCAR artifact identities remain separate."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.omat24.license-protocol",
        "af404e91e6c4fa64877b3a528f67a1f404f4cb826019b50c9fd79532d32ba567",
        "rename",
        replacement_id="fairchem.dataset.omat24.reference-protocol",
        replacement_text="OMat24 reference protocol",
        expected_scope_statement=(
            "The exact OMat24 page states CC-BY-4.0 dataset terms and VASP 5.4 "
            "PBE/PBE+U reference calculations; pseudopotential and raw-output "
            "rights are not inherited."
        ),
        replacement_statement=(
            "The exact OMat24 page records VASP 5.4 PBE/PBE+U reference "
            "calculations; pseudopotential and raw-output identities remain separate."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.odac23.license-protocol",
        "2a8db0d3a22cc3fc9b5810c6d27d792590f9520a3006f100853b9a9719cd9618",
        "rename",
        replacement_id="fairchem.dataset.odac23.reference-protocol",
        replacement_text="ODAC23 reference protocol",
        expected_scope_statement=(
            "The exact ODAC23 page states CC-BY-4.0 dataset terms and VASP 5.4 "
            "PBE+D3 reference calculations; gated storage and reference artifacts "
            "remain separate."
        ),
        replacement_statement=(
            "The exact ODAC23 page records VASP 5.4 PBE+D3 reference calculations; "
            "gated storage and reference artifact identities remain separate."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.oc20.license-protocol",
        "d460a825e577591259101d0124e9001eecad04e162775e00723e0d6a30d79b09",
        "rename",
        replacement_id="fairchem.dataset.oc20.reference-protocol",
        replacement_text="OC20 reference protocol",
        expected_scope_statement=(
            "The exact OC20 page states CC-BY-4.0 dataset terms and VASP 5.4 RPBE "
            "reference calculations; this is not a license for VASP, PAW/POTCAR "
            "contents, or raw outputs."
        ),
        replacement_statement=(
            "The exact OC20 page records VASP 5.4 RPBE reference calculations; VASP, "
            "PAW/POTCAR, and raw-output identities remain separate."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.oc22.license-protocol",
        "7e82bdfd3a0f6870a36c27faefa1711a2b5b565ca470d4a9c7e77cfaf442e993",
        "rename",
        replacement_id="fairchem.dataset.oc22.reference-protocol",
        replacement_text="OC22 reference protocol",
        expected_scope_statement=(
            "The exact OC22 page states CC-BY-4.0 dataset terms and VASP 5.4 PBE+U "
            "reference calculations; software, pseudopotential and raw-output rights "
            "remain separate."
        ),
        replacement_statement=(
            "The exact OC22 page records VASP 5.4 PBE+U reference calculations; "
            "software, pseudopotential, and raw-output identities remain separate."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.oc25.license-protocol",
        "7048ddad414cc2f0fb4a49f65570725bfebf049a4e2837624be35601397ea059",
        "rename",
        replacement_id="fairchem.dataset.oc25.reference-protocol",
        replacement_text="OC25 reference protocol",
        expected_scope_statement=(
            "The exact OC25 page states CC-BY-4.0 dataset terms and VASP 6.4 "
            "RPBE+D3 reference calculations; external access and artifact rights "
            "remain independently gated."
        ),
        replacement_statement=(
            "The exact OC25 page records VASP 6.4 RPBE+D3 reference calculations; "
            "external access and artifact identities remain independently gated."
        ),
    ),
    _legacy_action(
        "subject", "fairchem-datasets",
        "fairchem.dataset.rights.four-layer",
        "cf6a267c04fcb926d5874a0087a3e48a72a05f7dfa6292c63d2653a029c5ffcb",
        "rename",
        replacement_id="fairchem.dataset.identities.four-layer",
        replacement_text="Framework/model/data/reference-DFT identity separation",
        expected_scope_statement=(
            "FairChem framework source, UMA model artifacts, dataset distributions, "
            "and reference-DFT software/pseudopotential/raw-output materials require "
            "four independent identity and rights records."
        ),
        replacement_statement=(
            "FairChem framework source, UMA model artifacts, dataset distributions, "
            "and reference-DFT software/pseudopotential/raw-output materials require "
            "four independent identity and provenance records."
        ),
    ),
    _legacy_action(
        "subject", "ovito-docs", "provider.edition-license-separation",
        "dfb195041beacd546d00b75166a0c19c5bc41029732ae3033ed7bf3cbaaf98f9",
        "rename",
        replacement_id="provider.edition-identity-separation",
        replacement_text=(
            "Python module, Basic desktop, Pro desktop, source documentation, "
            "third-party notices, user data, and generated artifacts have distinct "
            "identity boundaries."
        ),
        expected_scope_statement=(
            "Python module, Basic desktop, Pro desktop, source documentation, "
            "third-party notices, user data, and generated artifacts have distinct "
            "identity and license boundaries."
        ),
        replacement_statement=(
            "Python module, Basic desktop, Pro desktop, source documentation, "
            "third-party notices, user data, and generated artifacts have distinct "
            "identity and provenance boundaries."
        ),
    ),
    _legacy_action(
        "subject", "ovito-docs", "license.documentation-gfdl",
        "fb6ef8db7bc572e1133d4e90eb1d5fc452fdb1e667fcc28a251855fa4d23099e",
        "rename",
        replacement_id="documentation.source-component-identity",
        replacement_text="OVITO documentation source-component identity",
        expected_scope_statement=(
            "The exact v3.15.5 source repository declares OVITO user documentation "
            "under GFDL-1.2-or-later while software and third-party components have "
            "separate terms."
        ),
        replacement_statement=(
            "The exact v3.15.5 source repository identifies OVITO user documentation "
            "as a distinct component from software and third-party artifacts."
        ),
    ),
    _legacy_action(
        "subject", "ovito-pypi", "provider.edition-license-separation",
        "af7be2ff4283271f13af7d281d5a50f0d0c5e8cda5560b87c97d4473557117de",
        "rename",
        replacement_id="provider.edition-identity-separation",
        replacement_text=(
            "Python module, Basic desktop, Pro desktop, source documentation, "
            "third-party notices, user data, and generated artifacts have distinct "
            "identity boundaries."
        ),
        expected_scope_statement=(
            "Python module, Basic desktop, Pro desktop, source documentation, "
            "third-party notices, user data, and generated artifacts have distinct "
            "identity and license boundaries."
        ),
        replacement_statement=(
            "Python module, Basic desktop, Pro desktop, source documentation, "
            "third-party notices, user data, and generated artifacts have distinct "
            "identity and provenance boundaries."
        ),
    ),
    _legacy_action(
        "subject", "vaspkit-docs", "site.installation-and-terms",
        "8a083dc9913a81820fb7c8f9ddd43734fd5c3c5a7eed45c01d5bfa3452a57301",
        "rename",
        replacement_id="site.installation-and-runtime-artifacts",
        replacement_text="VASPKIT installation and runtime-artifact evidence",
        expected_scope_statement=(
            "VASPKIT installation, binary distribution, platform, dependency, "
            "configuration, usage-agreement, and current terms claims require exact "
            "review of the installation page and binary archive."
        ),
        replacement_statement=(
            "VASPKIT installation, binary distribution, platform, dependency, and "
            "configuration claims require exact review of the installation page and "
            "selected binary archive identity."
        ),
    ),
    # Limitations: drop=2, rewrite=10.
    _legacy_action(
        "limitation", "iucr-cif-standards",
        "CIF dictionary redistribution terms remain unresolved.", None, "drop",
    ),
    _legacy_action(
        "limitation", "cp2k-2026-2-postprocess",
        "The manual documentation-license scope and CP2K external-tool repositories remain separate.",
        None, "rewrite",
        replacement_text=(
            "The manual documentation corpus and CP2K external-tool repositories "
            "remain separate technical authorities."
        ),
    ),
    _legacy_action(
        "limitation", "vasp-wiki-postprocess",
        "Wiki revisions do not establish VASP executable or POTCAR rights.",
        None, "rewrite",
        replacement_text=(
            "Wiki revisions do not establish a VASP executable or POTCAR byte identity."
        ),
    ),
    _legacy_action(
        "limitation", "vaspkit-docs",
        "The documentation commit does not establish exact binary identity or redistribution rights.",
        None, "rewrite",
        replacement_text=(
            "The documentation commit does not establish an exact binary identity."
        ),
    ),
    _legacy_action(
        "limitation", "gaussian-g16-c01-public",
        "This metadata-only catalog does not store page text, licensed manuals, examples, basis payloads, binaries, checkpoints, or user data.",
        None, "rewrite",
        replacement_text=(
            "This metadata-only catalog does not store page text, private manuals, "
            "examples, basis payloads, binaries, checkpoints, or user data."
        ),
    ),
    _legacy_action(
        "limitation", "gaussian-g16-c02-delta",
        "No licensed manual, installer, binary, example, basis payload, or checkpoint is stored.",
        None, "rewrite",
        replacement_text=(
            "No private manual, installer, binary, example, basis payload, or "
            "checkpoint is stored."
        ),
    ),
    _legacy_action(
        "limitation", "gpumd-docs",
        "The exact source-tree inventory does not establish a native GPU build, binary behavior, model/data licensing, NEP transferability, transport convergence, or scientific acceptance.",
        None, "rewrite",
        replacement_text=(
            "The exact source-tree inventory does not establish a native GPU build, "
            "binary behavior, selected model/data identities, NEP transferability, "
            "transport convergence, or scientific acceptance."
        ),
    ),
    _legacy_action(
        "limitation", "fairchem-v1",
        "Legacy checkpoint licenses remain unresolved.", None, "drop",
    ),
    _legacy_action(
        "limitation", "fairchem-datasets",
        "No proprietary software, pseudopotential, raw-output, model-weight, or gated-storage right is granted.",
        None, "rewrite",
        replacement_text=(
            "No software, pseudopotential, raw-output, model-weight, or gated-storage "
            "artifact identity is included."
        ),
    ),
    _legacy_action(
        "limitation", "multiwfn-manual",
        "Multiwfn manual and quick-start content are restricted to external-only receipts; the inventory does not establish a secure retrieval route, complete official-site universe, page/section coverage, executable identity, native behavior, scientific validity, or permission to redistribute derived manual content.",
        None, "rewrite",
        replacement_text=(
            "Multiwfn manual and quick-start content are represented by external-only "
            "receipts; the inventory does not establish a secure retrieval route, "
            "complete official-site universe, page/section coverage, executable "
            "identity, native behavior, or scientific validity."
        ),
    ),
    _legacy_action(
        "limitation", "siesta-portal",
        "Portal documentation authority and 5.4.2 release-source authority remain separate corpora and license reviews.",
        None, "rewrite",
        replacement_text=(
            "Portal documentation authority and 5.4.2 release-source authority "
            "remain separate technical corpora."
        ),
    ),
    _legacy_action(
        "limitation", "vaspkit-docs",
        "Two exact raw pages are hash-verified, and the full docs tree is path/object inventoried, but the remaining page bodies, semantic heading slices, build replay, documentation license, exact binary, private configuration, POTCAR, and parent VASP evidence remain external.",
        None, "rewrite",
        replacement_text=(
            "Two exact raw pages are hash-verified, and the full docs tree is "
            "path/object inventoried, but the remaining page bodies, semantic "
            "heading slices, build replay, exact binary, private configuration, "
            "POTCAR, and parent VASP evidence remain external."
        ),
    ),
    # Reviewed exclusion rationales: rewrite=2.
    _legacy_action(
        "exclusion", "mace-framework",
        "mace-rolling-docs-separate-authority",
        "30e7413c851ccab090951f191e17471a352b17abccf76920c31be0b1d6aec2d3",
        "rewrite",
        replacement_text=(
            "Documentation is version-divergent and is reviewed under the mace-docs "
            "provider input rather than silently merged with framework v0.3.16."
        ),
    ),
    _legacy_action(
        "exclusion", "uma-models", "uma-gated-model-card",
        "e71223f338bbd74bb4186da8a4808fad3b10bbf5a8f7be914d23c527d466b798",
        "rewrite",
        replacement_text="The raw card requires gated access and was not retrieved.",
    ),
)


_LEGACY_ACTION_INDEX = {
    (action.record_type, action.provider_input_id, action.record_id): action
    for action in LEGACY_RECORD_ACTIONS
}
if len(_LEGACY_ACTION_INDEX) != len(LEGACY_RECORD_ACTIONS):
    raise RuntimeError("duplicate exact legacy-record ledger entry")


CATALOG_WIDE_TECHNICAL_BINDINGS: dict[str, dict[str, str]] = {
    "repository-contracts-hpc": {
        "source_id": "hpc-repository-source-index",
        "subject_id": "repository-interface.catalog-wide-provenance",
        "statement": (
            "The exact dft-hpc-execution repository source-index receipt is the "
            "catalog-wide provider evidence for repository-interface provenance."
        ),
    },
    "repository-contracts-orchestrator": {
        "source_id": "orchestrator-repository-source-index",
        "subject_id": "repository-interface.catalog-wide-provenance",
        "statement": (
            "The exact dft-project-orchestrator repository source-index receipt is "
            "the catalog-wide provider evidence for repository-interface provenance."
        ),
    },
    "repository-contracts-reporting": {
        "source_id": "reporting-repository-source-index",
        "subject_id": "repository-interface.catalog-wide-provenance",
        "statement": (
            "The exact dft-reporting repository source-index receipt is the "
            "catalog-wide provider evidence for repository-interface provenance."
        ),
    },
    "repository-contracts-review-response": {
        "source_id": "review-response-repository-source-index",
        "subject_id": "repository-interface.catalog-wide-provenance",
        "statement": (
            "The exact dft-review-response repository source-index receipt is the "
            "catalog-wide provider evidence for repository-interface provenance."
        ),
    },
    "repository-contracts-literature-plan": {
        "source_id": "literature-plan-repository-source-index",
        "subject_id": "repository-interface.catalog-wide-provenance",
        "statement": (
            "The exact literature-to-dft-plan repository source-index receipt is the "
            "catalog-wide provider evidence for repository-interface provenance."
        ),
    },
}


class MigrationError(ValueError):
    """Structured conversion failure with machine-readable context."""

    def __init__(self, code: str, location: str, message: str) -> None:
        super().__init__(f"{code}: {location}: {message}")
        self.code = code
        self.location = location
        self.message = message


def canonical_json_bytes(value: Any) -> bytes:
    """Return repository canonical JSON bytes."""
    return canonical_projection_bytes(value) + b"\n"


def canonical_projection_bytes(value: Any) -> bytes:
    """Return repository canonical bytes used for hash identity."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    ).encode("utf-8")


def _assert_selector_id_unique(
    selector_id: str,
    seen_selector_ids: set[str],
    location: str,
) -> None:
    _require(selector_id not in seen_selector_ids, "SLICE_ID_DUPLICATE", location, "slice_id must be unique globally")
    seen_selector_ids.add(selector_id)


def _require_distinct_strings(values: list[Any], code: str, location: str) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not _is_str(value):
            _require(False, code, location, "entries must be strings")
        normalized_value = str(value)
        _require(
            normalized_value not in normalized,
            "RECORD_DUPLICATE_VALUE",
            location,
            "duplicate entries are not allowed",
        )
        normalized.append(normalized_value)
    return normalized


def _subject_from_catalog(subject: dict[str, Any], subject_id: str) -> dict[str, Any]:
    title = _require_non_empty(subject.get("title"), "OLD_SUBJECT_TITLE_MISSING", f"/catalog/subjects/{subject_id}/title", "title required")
    category = _require_non_empty(subject.get("category"), "OLD_SUBJECT_CATEGORY_MISSING", f"/catalog/subjects/{subject_id}/category", "category required")
    requirement_strength = _require_non_empty(
        subject.get("requirement_strength"),
        "OLD_SUBJECT_REQUIREMENT_STRENGTH_MISSING",
        f"/catalog/subjects/{subject_id}/requirement_strength",
        "requirement_strength required",
    )
    return {
        "title": title[:500],
        "category": category,
        "requirement_strength": requirement_strength,
    }


def _verify_raw_bytes(raw_bytes: Any, location: str) -> int:
    _require(isinstance(raw_bytes, int) and not isinstance(raw_bytes, bool), "SOURCE_BYTES_TYPE", location, "bytes must be non-boolean int")
    _require(raw_bytes > 0, "SOURCE_BYTES_INVALID", location, "bytes must be positive int")
    return int(raw_bytes)


def _normalize_preimage_bytes(preimage: Any, location: str) -> bytes:
    if isinstance(preimage, bytes):
        return preimage
    if isinstance(preimage, bytearray):
        return bytes(preimage)
    _require(_is_str(preimage), "INVENTORY_PREIMAGE_TYPE", location, "canonical preimage must be bytes or text")
    return str(preimage).encode("utf-8")


def _normalize_text(value: Any) -> str:
    _require_non_empty(value, "TYPE_TEXT_EMPTY", "/statement", "text must be non-empty")
    text = str(value).strip()
    return text[:2000]


def _coerce_exact_description(
    value: Any,
    fixed_map: dict[str, str],
    fallback: str,
) -> str:
    if _is_str(value):
        candidate = str(value).strip()
        if candidate in fixed_map:
            return fixed_map[candidate]
        if candidate != "":
            return candidate[:2000]
    return _normalize_text(fallback)


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _make_identity(payload: Any) -> dict[str, Any]:
    raw = canonical_json_bytes(payload)
    return {"sha256": _sha256_hex(raw), "bytes": len(raw)}


class _LegacyLedgerTracker:
    """Require exact, single consumption of this provider's reviewed actions."""

    def __init__(
        self,
        provider_input_id: str,
        catalog: dict[str, Any],
    ) -> None:
        self.provider_input_id = provider_input_id
        identities = {
            "blocker": {
                item.get("code")
                for item in catalog.get("blockers", [])
                if isinstance(item, dict)
            },
            "loss": {
                item.get("loss_id")
                for item in catalog.get("losses", [])
                if isinstance(item, dict)
            },
            "subject": {
                item.get("subject_id")
                for item in catalog.get("subjects", [])
                if isinstance(item, dict)
            },
            "limitation": {
                item
                for item in catalog.get("limitations", [])
                if isinstance(item, str)
            },
            "exclusion": {
                item.get("source_id")
                for item in catalog.get("reviewed_exclusions", [])
                if isinstance(item, dict)
            },
        }
        self.actions = tuple(
            action
            for action in LEGACY_RECORD_ACTIONS
            if action.provider_input_id == provider_input_id
            and action.record_id in identities[action.record_type]
        )
        self.catalog_hits: dict[LegacyRecordAction, int] = {}
        self.scope_hits: dict[LegacyRecordAction, int] = {}

    def action_for(
        self,
        record_type: str,
        record_id: str,
    ) -> LegacyRecordAction | None:
        return _LEGACY_ACTION_INDEX.get(
            (record_type, self.provider_input_id, record_id)
        )

    def consume_catalog_record(
        self,
        record_type: str,
        record_id: str,
        record: dict[str, Any],
        location: str,
    ) -> LegacyRecordAction | None:
        action = self.action_for(record_type, record_id)
        if action is None:
            return None
        _require(
            action.expected_sha256 is not None
            and _sha256_hex(canonical_projection_bytes(record))
            == action.expected_sha256,
            "LEGACY_LEDGER_RECORD_DRIFT",
            location,
            "reviewed exact legacy record no longer matches its canonical hash",
        )
        self.catalog_hits[action] = self.catalog_hits.get(action, 0) + 1
        _require(
            self.catalog_hits[action] == 1,
            "LEGACY_LEDGER_RECORD_DUPLICATE",
            location,
            "reviewed exact legacy record must occur once",
        )
        return action

    def consume_limitation(
        self,
        text_value: str,
        location: str,
    ) -> LegacyRecordAction | None:
        action = self.action_for("limitation", text_value)
        if action is None:
            return None
        self.catalog_hits[action] = self.catalog_hits.get(action, 0) + 1
        _require(
            self.catalog_hits[action] == 1,
            "LEGACY_LEDGER_RECORD_DUPLICATE",
            location,
            "reviewed exact legacy limitation must occur once",
        )
        return action

    def consume_subject_scope(
        self,
        subject_id: str,
        statement: str,
        location: str,
    ) -> LegacyRecordAction | None:
        action = self.action_for("subject", subject_id)
        if action is None:
            return None
        _require(
            statement == action.expected_scope_statement,
            "LEGACY_LEDGER_SCOPE_DRIFT",
            location,
            "reviewed subject scope statement no longer matches",
        )
        self.scope_hits[action] = self.scope_hits.get(action, 0) + 1
        _require(
            self.scope_hits[action] == 1,
            "LEGACY_LEDGER_SCOPE_DUPLICATE",
            location,
            "reviewed subject scope statement must occur once per provider input",
        )
        return action

    def verify_complete(self) -> None:
        for action in self.actions:
            _require(
                self.catalog_hits.get(action, 0) == 1,
                "LEGACY_LEDGER_ENTRY_UNCONSUMED",
                (
                    f"/legacy-ledger/{action.record_type}/"
                    f"{action.provider_input_id}/{action.record_id}"
                ),
                "reviewed exact legacy action was not consumed exactly once",
            )
            if action.record_type == "subject":
                _require(
                    self.scope_hits.get(action, 0) == 1,
                    "LEGACY_LEDGER_SCOPE_UNCONSUMED",
                    (
                        f"/legacy-ledger/subject/"
                        f"{action.provider_input_id}/{action.record_id}"
                    ),
                    "reviewed subject scope action was not consumed exactly once",
                )


def _require(condition: bool, code: str, location: str, message: str) -> None:
    if not condition:
        raise MigrationError(code, location, message)


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


def _require_non_empty(value: Any, code: str, location: str, message: str) -> str:
    _require(_is_str(value) and value.strip() != "", code, location, message)
    return value.strip()


def _safe_copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _require_mapping(value: Any, code: str, location: str) -> dict[str, Any]:
    _require(isinstance(value, dict), code, location, "must be a mapping")
    return value


def _require_list(value: Any, code: str, location: str) -> list[Any]:
    _require(isinstance(value, list), code, location, "must be an array")
    return value


def _extract_provider(input_value: Any) -> tuple[str, str]:
    provider = _require_mapping(input_value, "PROVIDER_TYPE", "/provider")
    provider_id = _require_non_empty(
        provider.get("provider_id"),
        "PROVIDER_ID_MISSING",
        "/provider/provider_id",
        "provider_id required",
    )
    provider_input_id = _require_non_empty(
        provider.get("provider_input_id") or provider.get("input_id"),
        "PROVIDER_INPUT_ID_MISSING",
        "/provider/provider_input_id",
        "provider_input_id or input_id required",
    )
    _require(SAFE_ID_RE.fullmatch(provider_id) is not None, "PROVIDER_ID_INVALID", "/provider/provider_id", "provider_id must be hyphen-safe id")
    _require(
        SAFE_ID_RE.fullmatch(provider_input_id) is not None,
        "PROVIDER_INPUT_ID_INVALID",
        "/provider/provider_input_id",
        "provider_input_id must be safe id",
    )
    return provider_id, provider_input_id


def _extract_authority(input_value: Any) -> str:
    if isinstance(input_value, str):
        authority_id = input_value
    else:
        authority = _require_mapping(input_value, "AUTHORITY_TYPE", "/authority")
        authority_id = authority.get("authority_id")
    authority_id = _require_non_empty(
        authority_id,
        "AUTHORITY_ID_MISSING",
        "/authority/authority_id",
        "authority_id required",
    )
    _require(SAFE_ID_RE.fullmatch(authority_id) is not None, "AUTHORITY_ID_INVALID", "/authority/authority_id", "authority_id must be hyphen-safe id")
    return authority_id


def _extract_authority_root(
    authority_projection: Any,
    inventory_locator: str,
) -> str:
    projection = _require_mapping(authority_projection, "AUTHORITY_PROJECTION_TYPE", "/authority_projection")
    canonical_urls = _require_list(
        projection.get("canonical_urls"),
        "AUTHORITY_CANONICAL_URLS_TYPE",
        "/authority_projection/canonical_urls",
    )
    canonical_urls = [
        str(item)
        for item in canonical_urls
        if isinstance(item, str) and HTTPS_URL_RE.match(item) is not None
    ]
    _require(canonical_urls, "AUTHORITY_CANONICAL_URLS_MISSING", "/authority_projection/canonical_urls", "non-empty canonical_urls required")

    candidates = [url for url in canonical_urls if inventory_locator.startswith(url)]
    _require(
        len(candidates) > 0,
        "AUTHORITY_ROOT_MISSING",
        "/authority_projection/canonical_urls",
        "inventory_projection locator is not covered by canonical_urls",
    )
    max_len = max(len(item) for item in candidates)
    longest = [item for item in candidates if len(item) == max_len]
    _require(
        len(longest) == 1,
        "AUTHORITY_ROOT_AMBIGUOUS",
        "/authority_projection/canonical_urls",
        "inventory_projection locator has multiple longest canonical URL prefixes",
    )
    return longest[0]


def _require_locator_in_authority_urls(
    canonical_urls: list[str],
    locator: str,
    location: str,
) -> None:
    _require(
        any(locator.startswith(url) for url in canonical_urls),
        "AUTHORITY_ROOT_MISSING",
        location,
        "locator is not covered by authority canonical_urls",
    )


def _require_registered_version_scope(
    scope: dict[str, Any],
    authority_projection: dict[str, Any],
) -> tuple[str, Any]:
    _require(
        isinstance(scope.get("kind"), str) and scope["kind"] in VERSION_SCOPE_KINDS,
        "VERSION_SCOPE_KIND_INVALID",
        "/version_scope/kind",
        "unsupported version_scope kind",
    )
    kind = scope["kind"]

    registered = _require_list(
        authority_projection.get("version_scopes"),
        "VERSION_SCOPE_REGISTRY_TYPE",
        "/authority_projection/version_scopes",
    )

    def match(record: dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            return False
        if kind in {"exact", "revision"}:
            if record.get("scope") not in {"exact", "revision"}:
                return False
            exact_version = record.get("exact_version")
            return isinstance(exact_version, str) and exact_version == scope.get("value")
        if kind == "release-line":
            return (
                record.get("scope") in {"release-series", "release_series", "release-line"}
                and record.get("release_series") == scope.get("value")
            )
        if kind == "latest-at-retrieval":
            return record.get("scope") == "latest-at-retrieval"
        if kind == "unversioned":
            return record.get("scope") == "unversioned"
        return False

    candidates = [item for item in registered if match(item)]
    _require(len(candidates) == 1, "VERSION_SCOPE_UNIQUE_MISMATCH", "/version_scope", "version_scope must have exactly one registry match")
    return kind, _safe_copy(candidates[0])


def _project_version_scope(scope: Any, authority_projection: Any) -> dict[str, Any]:
    version_scope = _require_mapping(scope, "VERSION_SCOPE_TYPE", "/version_scope")
    input_kind = version_scope.get("kind")
    kind, _matched_scope = _require_registered_version_scope(
        version_scope,
        _require_mapping(authority_projection, "AUTHORITY_PROJECTION_TYPE", "/authority_projection"),
    )
    if input_kind == "revision" and kind == "revision":
        exact_version = _matched_scope.get("exact_version")
        value = version_scope.get("value")
        if exact_version is not None and str(value) == str(exact_version):
            kind = "exact"

    value = version_scope.get("value")
    retrieved_utc = version_scope.get("retrieved_utc")

    if kind in {"exact", "revision", "release-line"}:
        _require(_is_str(value) and value.strip() != "", "VERSION_SCOPE_VALUE_MISSING", "/version_scope/value", "value required")
        return {
            "kind": kind,
            "value": str(value),
            "retrieved_utc": None,
            "snapshot_identity": None,
        }

    if kind == "unversioned":
        return {
            "kind": "unversioned",
            "value": None,
            "retrieved_utc": None,
            "snapshot_identity": None,
        }

    _require(kind == "latest-at-retrieval", "VERSION_SCOPE_KIND_INVALID", "/version_scope/kind", "latest-at-retrieval required")
    _require(_is_str(retrieved_utc) and retrieved_utc.strip() != "", "VERSION_SCOPE_RETRIEVED_UTC_MISSING", "/version_scope/retrieved_utc", "latest-at-retrieval requires retrieved_utc")

    return {
        "kind": "latest-at-retrieval",
        "value": None,
        "retrieved_utc": str(retrieved_utc).strip(),
        "snapshot_identity": None,
    }


def _subject_category_from_scope(value: str) -> str:
    mapping = {
        "claim": "scientific-limitation",
        "documented-claim": "scientific-limitation",
        "capability": "workflow",
        "task": "workflow",
        "workflow": "workflow",
        "executable": "workflow",
        "parameter": "input-parameter",
        "input-keyword": "input-parameter",
        "output-field": "output-observable",
        "observable": "output-observable",
        "backend": "provenance",
        "limitation": "scientific-limitation",
    }
    return mapping.get(value, "other")


def _subject_requirement_strength(disposition: Any) -> str:
    value = str(disposition) if _is_str(disposition) else "covered"
    if value == "partial":
        return "supporting"
    if value == "blocked":
        return "required"
    return "required"


def _build_scope_subjects(
    scope_catalog: Any,
    provider_input_id: str,
    tracker: _LegacyLedgerTracker,
) -> dict[str, dict[str, Any]]:
    scope = _require_mapping(scope_catalog, "SCOPE_CATALOG_TYPE", "/scope_catalog")
    subjects = _require_list(scope.get("subjects"), "SCOPE_SUBJECTS_TYPE", "/scope_catalog/subjects")

    output: dict[str, dict[str, Any]] = {}
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        if subject.get("evidence_class") != "official-provider-required":
            continue
        provider_input_ids = _require_list(subject.get("provider_input_ids"), "SCOPE_PROVIDER_INPUT_IDS_TYPE", "/scope_catalog/subjects/provider_input_ids")
        provider_ids = [str(item) for item in provider_input_ids if _is_str(item)]
        if provider_input_id not in provider_ids:
            continue
        subject_id = _require_non_empty(subject.get("subject_id"), "SCOPE_SUBJECT_ID_MISSING", "/scope_catalog/subjects/subject_id", "subject_id required")
        _require(SAFE_ID_RE.fullmatch(subject_id) is not None, "SCOPE_SUBJECT_ID_INVALID", f"/scope_catalog/subjects/{subject_id}", "subject_id must be safe id")
        statement = _require_non_empty(subject.get("statement"), "SCOPE_SUBJECT_STATEMENT_MISSING", f"/scope_catalog/subjects/{subject_id}/statement", "statement required")
        action = tracker.consume_subject_scope(
            subject_id,
            statement,
            f"/scope_catalog/subjects/{subject_id}/statement",
        )
        if action is not None and action.action == "drop":
            continue
        mapped_id = (
            action.replacement_id
            if action is not None and action.action == "rename"
            else subject_id
        )
        mapped_statement = (
            action.replacement_statement
            if action is not None and action.action == "rename"
            else statement
        )
        _require(
            _is_str(mapped_id) and SAFE_ID_RE.fullmatch(str(mapped_id)) is not None,
            "LEGACY_LEDGER_REPLACEMENT_ID_INVALID",
            f"/scope_catalog/subjects/{subject_id}",
            "replacement subject id must be safe",
        )
        _require(
            _is_str(mapped_statement) and str(mapped_statement).strip() != "",
            "LEGACY_LEDGER_REPLACEMENT_TEXT_INVALID",
            f"/scope_catalog/subjects/{subject_id}/statement",
            "replacement subject statement must be non-empty",
        )
        _require(
            str(mapped_id) not in output,
            "SCOPE_SUBJECT_ID_DUPLICATE",
            f"/scope_catalog/subjects/{subject_id}",
            "subject id is duplicate after exact migration mapping",
        )
        output[str(mapped_id)] = {
            "statement": _normalize_text(mapped_statement),
            "_provider_input_ids": provider_ids,
            "_subject_id": str(mapped_id),
        }
    return output


def _normalize_receipt(kind: str, identity: Any, location: str) -> dict[str, Any]:
    source = _require_mapping(identity, "SOURCE_IDENTITY_TYPE", location)
    method = source.get("retrieval_method")
    if method not in {"https-get", "official-api", "git-object", "other"}:
        # deterministic fallback from legacy schema kind
        legacy = source.get("kind")
        if legacy == "external-receipt":
            method = "https-get"
        elif legacy == "revision":
            method = "git-object"
        else:
            method = "other"
    raw_sha256 = source.get("raw_sha256")
    raw_bytes = source.get("raw_bytes")
    retrieved_utc = source.get("retrieved_utc")
    _require(_is_str(raw_sha256) and SHA256_RE.fullmatch(raw_sha256), "SOURCE_IDENTITY_SHA256_INVALID", f"{location}/raw_sha256", "raw_sha256 must be sha256")
    raw_bytes = _verify_raw_bytes(raw_bytes, f"{location}/raw_bytes")
    _require(
        _is_str(retrieved_utc) and retrieved_utc.strip() != "",
        "SOURCE_IDENTITY_UTC_INVALID",
        f"{location}/retrieved_utc",
        "retrieved_utc required",
    )
    return {
        "retrieval_method": method,
        "retrieved_utc": str(retrieved_utc).strip(),
        "raw_sha256": str(raw_sha256),
        "raw_bytes": int(raw_bytes),
    }


def _as_content(
    source: dict[str, Any],
    source_id: str,
    exact_receipt: dict[str, Any],
) -> dict[str, Any]:
    locator = source.get("locator")
    _require(
        _is_str(locator) and HTTPS_URL_RE.match(locator) is not None,
        "SOURCE_LOCATOR_INVALID",
        f"/sources/{source_id}/locator",
        "locator must be HTTPS URL",
    )
    _require(
        source.get("external_identity") is not None,
        "SOURCE_EXTERNAL_IDENTITY_MISSING",
        f"/sources/{source_id}/external_identity",
        "v1.0 declarative included source requires exact external identity",
    )
    return {
        "content_mode": "external-content",
        "locator": locator,
        "receipt": _safe_copy(exact_receipt),
    }


def _project_authority_revision(
    legacy_authority_revision: Any,
    version_scope_kind: str,
    inventory_identity: dict[str, Any],
    snapshot_identity: dict[str, Any] | None = None,
) -> str:
    def _coerce_identity(value: Any) -> str | None:
        if isinstance(value, str):
            candidate = value.strip()
            return candidate or None
        if not isinstance(value, dict):
            return None
        for key in ("value", "revision", "content_sha256", "sha256", "sha"):
            candidate = _coerce_identity(value.get(key))
            if candidate is not None:
                return candidate
        nested = value.get("snapshot_identity")
        if isinstance(nested, dict):
            for key in ("value", "content_sha256", "sha256", "sha"):
                candidate = _coerce_identity(nested.get(key))
                if candidate is not None:
                    return candidate
        return None

    if version_scope_kind == "latest-at-retrieval":
        legacy_snapshot = _coerce_identity(legacy_authority_revision)
        if legacy_snapshot is not None:
            return legacy_snapshot
        _require(
            snapshot_identity is not None,
            "AUTHORITY_REVISION_MISSING",
            "/authority_revision",
            "authority_revision required for latest-at-retrieval when legacy snapshot is unavailable",
        )
        return str(snapshot_identity["sha256"])

    if version_scope_kind == "unversioned":
        legacy_revision = _coerce_identity(legacy_authority_revision)
        if legacy_revision is not None:
            return legacy_revision
        return str(inventory_identity["sha256"])

    legacy_revision = _coerce_identity(legacy_authority_revision)
    if legacy_revision is not None:
        return legacy_revision
    return str(inventory_identity["sha256"])


def _project_selector(
    source_id: str,
    slice_record: dict[str, Any],
    subject_renames: dict[str, str],
    subject_drop: set[str],
    loss_renames: dict[str, str],
    loss_drop: set[str],
    seen_selector_ids: set[str],
    source_external_identity: dict[str, Any],
    catalog_wide_subject_id: str | None,
) -> tuple[dict[str, Any], bool, dict[str, Any]]:
    selector = _require_mapping(slice_record.get("selector"), "SLICE_SELECTOR_TYPE", f"/sources/{source_id}/slices/selector")
    selector_id = _require_non_empty(
        slice_record.get("slice_id") or slice_record.get("selector_id"),
        "SLICE_ID_MISSING",
        f"/sources/{source_id}/slices/slice_id",
        "slice_id required",
    )
    _require(SAFE_ID_RE.fullmatch(selector_id) is not None, "SLICE_ID_INVALID", f"/sources/{source_id}/slices/{selector_id}/slice_id", "slice_id must be safe id")
    _assert_selector_id_unique(selector_id, seen_selector_ids, f"/sources/{source_id}/slices/{selector_id}/slice_id")
    kind = _require_non_empty(
        selector.get("kind"),
        "SLICE_KIND_MISSING",
        f"/sources/{source_id}/slices/{selector_id}/kind",
        "selector kind required",
    )
    layer = _require_non_empty(
        selector.get("layer"),
        "SLICE_LAYER_MISSING",
        f"/sources/{source_id}/slices/{selector_id}/layer",
        "slice layer required",
    )
    _require(layer in {"raw-source", "derived-artifact"}, "SLICE_LAYER_INVALID", f"/sources/{source_id}/slices/{selector_id}/layer", "layer invalid")
    if kind == "json-pointer" and layer in SELECTOR_LAYER_FIXES:
        layer = "derived-artifact"
    _require(kind in {"heading", "byte-range", "json-pointer", "line-range", "page-range", "whole-source", "source-symbol", "other"}, "SLICE_KIND_INVALID", f"/sources/{source_id}/slices/{selector_id}/kind", "selector kind invalid")
    if kind == "whole-source":
        _require(selector.get("value") == "*", "SLICE_WHOLE_SOURCE_VALUE", f"/sources/{source_id}/slices/{selector_id}/value", "whole-source value must be '*'")
    if kind == "byte-range":
        value = _require_non_empty(
            selector.get("value"),
            "SLICE_VALUE_MISSING",
            f"/sources/{source_id}/slices/{selector_id}/value",
            "byte-range value required",
        )
        _require(
            isinstance(value, str) and re.fullmatch(r"^(?:0|[1-9][0-9]*):[1-9][0-9]*$", value) is not None,
            "SLICE_BYTE_RANGE_VALUE_INVALID",
            f"/sources/{source_id}/slices/{selector_id}/value",
            "byte-range requires start:end",
        )
    else:
        value = _require_non_empty(
            selector.get("value"),
            "SLICE_VALUE_MISSING",
            f"/sources/{source_id}/slices/{selector_id}/value",
            "selector value required",
        )

    subject_ids = _require_list(
        slice_record.get("subject_ids"),
        "SLICE_SUBJECT_IDS_TYPE",
        f"/sources/{source_id}/slices/{selector_id}/subject_ids",
    )
    loss_ids = _require_list(
        slice_record.get("loss_ids", []),
        "SLICE_LOSS_IDS_TYPE",
        f"/sources/{source_id}/slices/{selector_id}/loss_ids",
    )

    normalized_subject_ids: list[str] = []
    for subject_id in _require_distinct_strings(
        subject_ids,
        "SLICE_SUBJECT_ID_DUPLICATE",
        f"/sources/{source_id}/slices/{selector_id}/subject_ids",
    ):
        if subject_id in subject_drop:
            continue
        mapped_subject_id = subject_renames.get(subject_id, subject_id)
        _require(
            mapped_subject_id not in normalized_subject_ids,
            "SLICE_SUBJECT_ID_DUPLICATE",
            f"/sources/{source_id}/slices/{selector_id}/subject_ids",
            "subject_ids must remain distinct after exact mapping",
        )
        normalized_subject_ids.append(mapped_subject_id)
    if not normalized_subject_ids and catalog_wide_subject_id is not None:
        normalized_subject_ids.append(catalog_wide_subject_id)

    normalized_losses: list[str] = []
    for loss_id in loss_ids:
        _require(_is_str(loss_id), "SLICE_LOSS_ID_INVALID", f"/sources/{source_id}/slices/{selector_id}/loss_ids", "loss id must be string")
        normalized = loss_renames.get(str(loss_id), str(loss_id))
        if normalized in loss_drop:
            continue
        _require(
            normalized not in normalized_losses,
            "SLICE_LOSS_ID_DUPLICATE",
            f"/sources/{source_id}/slices/{selector_id}/loss_ids",
            "loss_ids must not contain duplicates",
        )
        normalized_losses.append(normalized)

    external_receipt = _require_mapping(
        slice_record.get("external_receipt"),
        "SLICE_EXTERNAL_RECEIPT_TYPE",
        f"/sources/{source_id}/slices/{selector_id}/external_receipt",
    )
    exact_receipt = _normalize_receipt(
        "external-content",
        external_receipt,
        f"/sources/{source_id}/slices/{selector_id}/external_receipt",
    )
    for field in ("raw_sha256", "raw_bytes", "retrieved_utc"):
        _require(
            exact_receipt[field] == source_external_identity[field],
            "SLICE_RAW_RECEIPT_MISMATCH",
            f"/sources/{source_id}/slices/{selector_id}/external_receipt/{field}",
            "slice raw receipt must exactly match source external identity",
        )
    selected_sha = _require_non_empty(
        external_receipt.get("selected_sha256"),
        "SLICE_SELECTED_SHA256_MISSING",
        f"/sources/{source_id}/slices/{selector_id}/external_receipt/selected_sha256",
        "selected_sha256 required",
    )
    _require(
        SHA256_RE.fullmatch(selected_sha) is not None,
        "SLICE_SELECTED_SHA256_INVALID",
        f"/sources/{source_id}/slices/{selector_id}/external_receipt/selected_sha256",
        "selected_sha256 must be sha256",
    )
    selected_bytes = _verify_raw_bytes(
        external_receipt.get("selected_bytes"),
        f"/sources/{source_id}/slices/{selector_id}/external_receipt/selected_bytes",
    )
    if kind == "whole-source":
        _require(
            layer == "raw-source",
            "SLICE_WHOLE_SOURCE_LAYER_INVALID",
            f"/sources/{source_id}/slices/{selector_id}/layer",
            "whole-source selector must bind raw-source bytes",
        )
        _require(
            selected_sha == exact_receipt["raw_sha256"]
            and selected_bytes == exact_receipt["raw_bytes"],
            "SLICE_WHOLE_SOURCE_IDENTITY_MISMATCH",
            f"/sources/{source_id}/slices/{selector_id}/external_receipt",
            "whole-source selected identity must equal the raw source identity",
        )
    if kind == "json-pointer":
        _require(
            layer == "derived-artifact",
            "SLICE_JSON_POINTER_LAYER_INVALID",
            f"/sources/{source_id}/slices/{selector_id}/layer",
            "json-pointer selector must bind a derived artifact identity",
        )
    selected_identity = {"sha256": str(selected_sha), "bytes": int(selected_bytes)}

    return (
        {
            "selector_id": selector_id,
            "layer": layer,
            "kind": kind,
            "value": str(value),
            "subject_ids": normalized_subject_ids,
            "loss_ids": normalized_losses,
            "selected_identity": selected_identity,
        },
        kind == "json-pointer",
        exact_receipt,
    )


def _project_loss(
    loss: dict[str, Any],
    tracker: _LegacyLedgerTracker,
) -> tuple[str, dict[str, Any]] | None:
    loss_id = _require_non_empty(loss.get("loss_id"), "LOSS_ID_MISSING", "/losses/loss_id", "loss_id required")
    action = tracker.consume_catalog_record(
        "loss",
        loss_id,
        loss,
        f"/losses/{loss_id}",
    )
    if action is not None and action.action == "drop":
        return None
    mapped_id = (
        action.replacement_id
        if action is not None and action.action == "rename"
        else loss_id
    )
    _require(SAFE_ID_RE.fullmatch(mapped_id) is not None, "LOSS_ID_INVALID", "/losses/loss_id", "loss_id must be safe id")

    stage = loss.get("stage")
    materiality = loss.get("materiality")
    disposition = loss.get("disposition")
    affected_source_ids = _require_list(loss.get("affected_source_ids"), "LOSS_AFFECTED_SOURCE_IDS_TYPE", "/losses/affected_source_ids")
    _require(stage in {"discovery", "retrieval", "extraction", "normalization", "storage", "mapping", "other"}, "LOSS_STAGE_INVALID", "/losses/stage", "invalid loss stage")
    _require(materiality in {"none", "non-material", "material", "unknown"}, "LOSS_MATERIALITY_INVALID", "/losses/materiality", "invalid materiality")
    _require(disposition in {"accepted", "preserved", "external-only", "blocked"}, "LOSS_DISPOSITION_INVALID", "/losses/disposition", "invalid disposition")
    _require(affected_source_ids, "LOSS_AFFECTED_SOURCE_IDS_EMPTY", "/losses/affected_source_ids", "affected_source_ids must be non-empty")

    description = _normalize_text(loss.get("description"))
    if action is not None and action.action in {"rename", "rewrite"}:
        _require(
            _is_str(action.replacement_text)
            and str(action.replacement_text).strip() != "",
            "LEGACY_LEDGER_REPLACEMENT_TEXT_INVALID",
            f"/losses/{loss_id}/description",
            "mapped loss requires replacement description",
        )
        description = _normalize_text(action.replacement_text)

    mapped_sources = _require_distinct_strings(affected_source_ids, "LOSS_AFFECTED_SOURCE_ID_INVALID", "/losses/affected_source_ids")

    return mapped_id, {
        "stage": stage,
        "description": description,
        "materiality": materiality,
        "disposition": disposition,
        "affected_source_ids": sorted(mapped_sources),
    }


def _project_blockers(
    blockers: Any,
    tracker: _LegacyLedgerTracker,
) -> list[dict[str, Any]]:
    if not isinstance(blockers, list):
        return []
    normalized: list[dict[str, Any]] = []
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        code = blocker.get("code")
        _require(_is_str(code), "BLOCKER_CODE_MISSING", "/blockers/code", "blocker code required")
        original_code = str(code)
        action = tracker.consume_catalog_record(
            "blocker",
            original_code,
            blocker,
            f"/blockers/{original_code}",
        )
        if action is not None and action.action == "drop":
            continue
        code = (
            action.replacement_id
            if action is not None and action.action == "rename"
            else original_code
        )
        _require(
            _is_str(code) and SAFE_ID_RE.fullmatch(str(code)) is not None,
            "BLOCKER_CODE_INVALID",
            f"/blockers/{original_code}/code",
            "blocker code must be safe after exact migration mapping",
        )
        description = _normalize_text(blocker.get("description"))
        if action is not None and action.action in {"rename", "rewrite"}:
            _require(
                _is_str(action.replacement_text)
                and str(action.replacement_text).strip() != "",
                "LEGACY_LEDGER_REPLACEMENT_TEXT_INVALID",
                f"/blockers/{original_code}/description",
                "mapped blocker requires replacement description",
            )
            description = _normalize_text(action.replacement_text)
        dimensions = blocker.get("dimensions")
        if isinstance(dimensions, list):
            dimensions = [str(item) for item in dimensions if _is_str(item)]
            dimensions = sorted(set(dimensions))
        else:
            dimensions = []
        _require(len(dimensions) >= 1, "BLOCKER_DIMENSIONS_EMPTY", "/blockers/dimensions", "dimensions must be non-empty")
        normalized.append({"code": str(code), "description": description[:2000], "dimensions": dimensions})
    return normalized


def _project_limitation_from_exclusion(source_id: str, exclusion: dict[str, Any]) -> str:
    rationale = _require_non_empty(
        exclusion.get("rationale"),
        "EXCLUSION_RATIONALE_MISSING",
        f"/reviewed_exclusions/{source_id}/rationale",
        "rationale required",
    )
    return _coerce_exact_description(rationale, {}, "Reviewed exclusion rationale is technical and non-legal.")


def _project_reviewed_exclusion_rationale(
    source_id: str,
    exclusion: dict[str, Any],
    tracker: _LegacyLedgerTracker,
) -> str:
    rationale = _project_limitation_from_exclusion(source_id, exclusion)
    action = tracker.consume_catalog_record(
        "exclusion",
        source_id,
        exclusion,
        f"/reviewed_exclusions/{source_id}",
    )
    if action is None:
        return rationale
    _require(
        action.action == "rewrite"
        and _is_str(action.replacement_text)
        and str(action.replacement_text).strip() != "",
        "LEGACY_LEDGER_REPLACEMENT_TEXT_INVALID",
        f"/reviewed_exclusions/{source_id}/rationale",
        "reviewed exclusion action requires replacement rationale",
    )
    return _normalize_text(action.replacement_text)


def _build_catalog_subjects(
    catalog_subjects: Any,
    tracker: _LegacyLedgerTracker,
) -> dict[str, dict[str, str]]:
    if catalog_subjects is None:
        return {}
    subjects = _require_list(catalog_subjects, "CATALOG_SUBJECTS_TYPE", "/subjects")
    output: dict[str, dict[str, str]] = {}
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        subject_id = _require_non_empty(subject.get("subject_id"), "CATALOG_SUBJECT_ID_MISSING", "/subjects/subject_id", "subject_id required")
        _require(SAFE_ID_RE.fullmatch(subject_id) is not None, "CATALOG_SUBJECT_ID_INVALID", f"/subjects/{subject_id}", "subject_id must be safe id")
        subject_record = _require_mapping(
            subject,
            "CATALOG_SUBJECT_TYPE",
            f"/subjects/{subject_id}",
        )
        action = tracker.consume_catalog_record(
            "subject",
            subject_id,
            subject_record,
            f"/subjects/{subject_id}",
        )
        if action is not None and action.action == "drop":
            continue
        mapped_id = (
            action.replacement_id
            if action is not None and action.action == "rename"
            else subject_id
        )
        _require(
            _is_str(mapped_id) and SAFE_ID_RE.fullmatch(str(mapped_id)) is not None,
            "LEGACY_LEDGER_REPLACEMENT_ID_INVALID",
            f"/subjects/{subject_id}",
            "replacement subject id must be safe",
        )
        _require(str(mapped_id) not in output, "CATALOG_SUBJECT_DUPLICATE", f"/subjects/{subject_id}", "subject_id duplicate after exact mapping")
        projected = _subject_from_catalog(subject_record, subject_id)
        if action is not None and action.action == "rename":
            _require(
                _is_str(action.replacement_text)
                and str(action.replacement_text).strip() != "",
                "LEGACY_LEDGER_REPLACEMENT_TEXT_INVALID",
                f"/subjects/{subject_id}/title",
                "renamed subject requires replacement title",
            )
            projected["title"] = _normalize_text(action.replacement_text)[:500]
        output[str(mapped_id)] = projected
    return output


def _project_inventory_projection(inventory_projection: Any, authority_root: str) -> tuple[str, dict[str, Any]]:
    projection = _require_mapping(inventory_projection, "INVENTORY_PROJECTION_TYPE", "/inventory_projection")
    locator = _require_non_empty(projection.get("locator"), "INVENTORY_PROJECTION_LOCATOR_MISSING", "/inventory_projection/locator", "locator required")
    _require(HTTPS_URL_RE.match(locator) is not None, "INVENTORY_PROJECTION_LOCATOR_INVALID", "/inventory_projection/locator", "inventory_projection locator must be https URL")
    _require(locator.startswith(authority_root), "INVENTORY_PROJECTION_LOCATOR_SCOPE", "/inventory_projection/locator", "inventory_locator must match chosen authority_root prefix")

    provided_identity = _require_mapping(
        projection.get("identity"),
        "INVENTORY_PROJECTION_IDENTITY_MISSING",
        "/inventory_projection/identity",
    )
    identity_sha = _require_non_empty(
        provided_identity.get("sha256"),
        "INVENTORY_PROJECTION_IDENTITY_SHA256_MISSING",
        "/inventory_projection/identity/sha256",
        "identity.sha256 required",
    )
    _require(SHA256_RE.fullmatch(identity_sha), "INVENTORY_PROJECTION_IDENTITY_SHA256_INVALID", "/inventory_projection/identity/sha256", "identity.sha256 must be sha256")
    provided_bytes = _verify_raw_bytes(
        provided_identity.get("bytes"),
        "/inventory_projection/identity/bytes",
    )
    preimage = projection.get("canonical_preimage_bytes")
    _require(_is_str(preimage) or isinstance(preimage, (bytes, bytearray)), "INVENTORY_PROJECTION_PREIMAGE_MISSING", "/inventory_projection/canonical_preimage_bytes", "canonical_preimage_bytes required")
    preimage_bytes = _normalize_preimage_bytes(preimage, "/inventory_projection/canonical_preimage_bytes")
    _require(len(preimage_bytes) == provided_bytes, "INVENTORY_PREIMAGE_BYTES_MISMATCH", "/inventory_projection/canonical_preimage_bytes", "canonical_preimage_bytes length mismatch")
    _require(_sha256_hex(preimage_bytes) == identity_sha, "INVENTORY_PREIMAGE_SHA256_MISMATCH", "/inventory_projection/identity", "identity does not match canonical preimage bytes")
    return locator, {"sha256": identity_sha, "bytes": provided_bytes}


def _snapshot_from_sources_and_exclusions(
    discovered_sources: dict[str, Any],
) -> dict[str, Any]:
    aggregate_entries: list[dict[str, Any]] = []
    for source_id in sorted(discovered_sources):
        source = discovered_sources[source_id]
        if source["disposition"] != "included":
            aggregate_entries.append(
                {
                    "source_id": source_id,
                    "disposition": "excluded",
                    "inventory_entry_identity": source["content"]["inventory_entry_identity"],
                }
            )
            continue
        _require(
            source["content"]["content_mode"] == "external-content",
            "SOURCE_SNAPSHOT_SOURCE_MODE",
            f"/discovered_sources/{source_id}/content/content_mode",
            "latest-at-retrieval snapshot requires exact external-content sources",
        )
        aggregate_entries.append(
            {
                "source_id": source_id,
                "disposition": source["disposition"],
                "locator": source["content"]["locator"],
                "receipt": source["content"]["receipt"],
            }
        )
    return _canonical_snapshot_identity(aggregate_entries)


def _canonical_snapshot_identity(values: Any) -> dict[str, Any]:
    projection = canonical_projection_bytes(values)
    return {"sha256": _sha256_hex(projection), "bytes": len(projection)}


def _project_sources(
    sources: list[Any],
    subject_renames: dict[str, str],
    subject_drop: set[str],
    loss_renames: dict[str, str],
    loss_drop: set[str],
    valid_subjects: set[str],
    valid_losses: set[str],
    catalog_wide_binding: dict[str, str] | None,
) -> tuple[dict[str, Any], set[str], bool]:
    projected: dict[str, Any] = {}
    referenced_losses: set[str] = set()
    has_json_pointer = False

    seen_ids: set[str] = set()
    seen_selector_ids: set[str] = set()
    for source in sources:
        _require(isinstance(source, dict), "SOURCE_TYPE", "/sources", "each source must be mapping")
        source_id = _require_non_empty(source.get("source_id"), "SOURCE_ID_MISSING", "/sources/source_id", "source_id required")
        _require(source_id not in seen_ids, "SOURCE_ID_DUPLICATE", f"/sources/{source_id}", "source_id duplicate")
        _require(SOURCE_ID_RE.fullmatch(source_id) is not None, "SOURCE_ID_INVALID", f"/sources/{source_id}", "source_id must be source-id pattern")
        seen_ids.add(source_id)

        disposition = source.get("disposition")
        title = _require_non_empty(
            source.get("title"),
            "SOURCE_TITLE_MISSING",
            f"/sources/{source_id}/title",
            "title required",
        )
        source_kind = _require_non_empty(
            source.get("source_kind"),
            "SOURCE_KIND_MISSING",
            f"/sources/{source_id}/source_kind",
            "source_kind required",
        )

        if disposition == "excluded":
            reason_code = _require_non_empty(
                source.get("reason_code"),
                "SOURCE_REASON_CODE_MISSING",
                f"/sources/{source_id}/reason_code",
                "reason_code required",
            )
            _require(
                reason_code in {
                    "duplicate",
                    "out-of-scope",
                    "navigation-only",
                    "obsolete",
                    "generated-alias",
                    "unavailable",
                    "other",
                },
                "SOURCE_REASON_CODE_INVALID",
                f"/sources/{source_id}/reason_code",
                "invalid reason code",
            )
            projected[source_id] = {
                "disposition": "excluded",
                "title": title[:500],
                "source_kind": source_kind,
                "content": {
                    "content_mode": "excluded",
                    "locator": _require_non_empty(
                        source.get("locator"),
                        "SOURCE_EXCLUDED_LOCATOR_MISSING",
                        f"/sources/{source_id}/locator",
                        "locator required",
                    ),
                    "inventory_entry_identity": _make_identity(
                        {
                            "source_id": source_id,
                            "title": title,
                            "rationale": source.get("rationale"),
                        }
                    ),
                },
                "reason_code": reason_code,
                "rationale": _project_limitation_from_exclusion(source_id, source),
            }
            continue

        _require(disposition == "included", "SOURCE_DISPOSITION_INVALID", f"/sources/{source_id}/disposition", "disposition must be included or excluded")
        slices = _require_list(source.get("slices"), f"/sources/{source_id}/slices", "included source must have slices")
        _require(slices, "SOURCE_SLICES_EMPTY", f"/sources/{source_id}/slices", "included source must have non-empty slices")

        selectors: list[dict[str, Any]] = []
        source_external_identity = source.get("external_identity")
        external_identity = None
        if source_external_identity is not None:
            external_identity = _normalize_receipt("external-content", source_external_identity, f"/sources/{source_id}/external_identity")
            _require(external_identity["retrieval_method"] is not None, "SOURCE_EXTERNAL_RECEIPT_INVALID", f"/sources/{source_id}/external_identity", "external identity must contain retrieval metadata")
        _require(
            external_identity is not None,
            "SOURCE_EXTERNAL_IDENTITY_MISSING",
            f"/sources/{source_id}/external_identity",
            "included declarative source requires exact external identity",
        )
        source_subject_ids: list[str] = []
        source_losses: list[str] = []
        exact_receipts: list[dict[str, Any]] = []
        catalog_wide_subject_id = None
        if catalog_wide_binding is not None:
            _require(
                source_id == catalog_wide_binding["source_id"],
                "CATALOG_WIDE_BINDING_SOURCE_MISMATCH",
                f"/sources/{source_id}",
                "catalog-wide technical binding names a different source",
            )
            catalog_wide_subject_id = catalog_wide_binding["subject_id"]
        for slice_record in slices:
            selector, is_json_pointer, exact_receipt = _project_selector(
                source_id,
                _require_mapping(slice_record, "SLICE_TYPE", f"/sources/{source_id}/slices"),
                subject_renames,
                subject_drop,
                loss_renames,
                loss_drop,
                seen_selector_ids,
                external_identity,
                catalog_wide_subject_id,
            )
            exact_receipts.append(exact_receipt)
            has_json_pointer = has_json_pointer or is_json_pointer
            for sid in selector["subject_ids"]:
                _require(sid in valid_subjects, "SLICE_SUBJECT_UNKNOWN", f"/sources/{source_id}/selectors/{selector['selector_id']}/subject_ids/{sid}", "subject id missing in scope-bound subjects")
                _require(
                    sid not in source_subject_ids,
                    "SOURCE_SUBJECT_ID_DUPLICATE",
                    f"/sources/{source_id}/selectors/{selector['selector_id']}/subject_ids/{sid}",
                    "source subject_ids contains duplicates",
                )
                source_subject_ids.append(sid)
            for lid in selector["loss_ids"]:
                if lid in loss_drop:
                    continue
                _require(lid in valid_losses, "SLICE_LOSS_UNKNOWN", f"/sources/{source_id}/selectors/{selector['selector_id']}/loss_ids/{lid}", "loss id unknown")
                _require(
                    lid not in source_losses,
                    "SOURCE_LOSS_ID_DUPLICATE",
                    f"/sources/{source_id}/selectors/{selector['selector_id']}/loss_ids/{lid}",
                    "source loss_ids contains duplicates",
                )
                source_losses.append(lid)
            selectors.append(selector)
        _require(
            exact_receipts,
            "SOURCE_EXTERNAL_RECEIPT_MISSING",
            f"/sources/{source_id}/slices",
            "included declarative source requires exact slice receipt",
        )
        for exact_receipt in exact_receipts[1:]:
            _require(
                exact_receipt == exact_receipts[0],
                "SOURCE_RAW_RECEIPT_INCONSISTENT",
                f"/sources/{source_id}/slices",
                "all selectors for a source must bind one exact raw receipt",
            )

        content = _as_content(source, source_id, exact_receipts[0])
        _require(selectors, "SOURCE_SELECTOR_MISSING", f"/sources/{source_id}/selectors", "external source requires selectors")

        projected[source_id] = {
            "disposition": "included",
            "title": title[:500],
            "source_kind": source_kind,
            "content": content,
            "selectors": selectors,
            "subject_ids": source_subject_ids,
            "loss_ids": source_losses,
        }
        referenced_losses.update(source_losses)

    return projected, referenced_losses, has_json_pointer


def convert_catalog_v10_to_v11(
    catalog: Any,
    *,
    provider: Any,
    authority: Any,
    authority_projection: Any,
    scope_catalog: Any,
    inventory_projection: Any,
) -> dict[str, Any]:
    """Convert a parsed official-document-source-catalog@1.0 payload to @1.1."""

    input_catalog = _safe_copy(_require_mapping(catalog, "CATALOG_TYPE", "/catalog"))

    _require(input_catalog.get("schema_version") == "1.0", "CATALOG_VERSION_MISMATCH", "/catalog/schema_version", "catalog must be schema 1.0")
    _require(input_catalog.get("contract_name") == CONTRACT_NAME, "CATALOG_CONTRACT_MISMATCH", "/catalog/contract_name", "contract_name mismatch")

    sources = _require_list(input_catalog.get("sources"), "CATALOG_SOURCES_TYPE", "/sources")
    reviewed_exclusions = _require_list(input_catalog.get("reviewed_exclusions"), "CATALOG_REVIEWED_EXCLUSIONS_TYPE", "/reviewed_exclusions")
    losses = _require_list(input_catalog.get("losses"), "CATALOG_LOSSES_TYPE", "/losses")
    limitations = _require_list(input_catalog.get("limitations"), "CATALOG_LIMITATIONS_TYPE", "/limitations")
    blockers = _require_list(input_catalog.get("blockers"), "CATALOG_BLOCKERS_TYPE", "/blockers")
    version_scope_input = input_catalog.get("version_scope")
    _require(version_scope_input is not None, "CATALOG_VERSION_SCOPE_MISSING", "/version_scope", "version_scope required")
    inventory_locator = _require_non_empty(input_catalog.get("inventory_locator"), "CATALOG_INVENTORY_LOCATOR_MISSING", "/inventory_locator", "inventory_locator required")
    _require(HTTPS_URL_RE.match(inventory_locator) is not None, "CATALOG_INVENTORY_LOCATOR_INVALID", "/inventory_locator", "inventory_locator must be https URL")
    _require(isinstance(input_catalog.get("upstream_universe_complete"), bool), "CATALOG_UPSTREAM_TYPE", "/upstream_universe_complete", "must be bool")

    authority_id = _extract_authority(authority)
    provider_id, provider_input_id = _extract_provider(provider)
    tracker = _LegacyLedgerTracker(provider_input_id, input_catalog)
    authority_projection = _require_mapping(authority_projection, "AUTHORITY_PROJECTION_TYPE", "/authority_projection")
    canonical_urls = _require_list(
        authority_projection.get("canonical_urls"),
        "AUTHORITY_CANONICAL_URLS_TYPE",
        "/authority_projection/canonical_urls",
    )
    canonical_urls = [
        str(item)
        for item in canonical_urls
        if isinstance(item, str) and HTTPS_URL_RE.match(item) is not None
    ]
    _require(canonical_urls, "AUTHORITY_CANONICAL_URLS_MISSING", "/authority_projection/canonical_urls", "non-empty canonical_urls required")
    inventory_projection_map = _require_mapping(inventory_projection, "INVENTORY_PROJECTION_TYPE", "/inventory_projection")
    projected_locator = _require_non_empty(
        inventory_projection_map.get("locator"),
        "INVENTORY_PROJECTION_LOCATOR_MISSING",
        "/inventory_projection/locator",
        "locator required",
    )
    _require(
        HTTPS_URL_RE.match(projected_locator) is not None,
        "INVENTORY_PROJECTION_LOCATOR_INVALID",
        "/inventory_projection/locator",
        "inventory_projection locator must be https URL",
    )
    authority_root = _extract_authority_root(authority_projection, projected_locator)

    for source in sources:
        if not isinstance(source, dict):
            continue
        source_locator = source.get("locator")
        _require(
            _is_str(source_locator),
            "SOURCE_LOCATOR_MISSING",
            "/sources/locator",
            "source locator required",
        )
        _require_locator_in_authority_urls(
            canonical_urls,
            source_locator,
            f"/sources/{source.get('source_id')}/locator",
        )

    version_scope = _project_version_scope(
        _safe_copy(version_scope_input),
        _safe_copy(authority_projection),
    )

    # Scope-bound subjects only. Catalog subjects are ignored unless provider-bound.
    scope_subjects = _build_scope_subjects(
        scope_catalog,
        provider_input_id,
        tracker,
    )
    catalog_subjects = _build_catalog_subjects(
        input_catalog.get("subjects"),
        tracker,
    )
    _require(
        set(catalog_subjects.keys()) == set(scope_subjects.keys()),
        "SUBJECT_SET_MISMATCH",
        "/subjects",
        "catalog subjects and scope provider subjects must match exactly",
    )

    catalog_wide_binding = CATALOG_WIDE_TECHNICAL_BINDINGS.get(provider_input_id)
    if catalog_wide_binding is not None:
        _require(
            not catalog_subjects and not scope_subjects,
            "CATALOG_WIDE_BINDING_SCOPE_MISMATCH",
            "/subjects",
            "catalog-wide technical binding requires an empty legacy subject set",
        )
        binding_subject_id = catalog_wide_binding["subject_id"]
        catalog_subjects[binding_subject_id] = {
            "title": "Catalog-wide repository-interface provenance",
            "category": "provenance",
            "requirement_strength": "supporting",
        }
        scope_subjects[binding_subject_id] = {
            "statement": catalog_wide_binding["statement"],
            "_provider_input_ids": [provider_input_id],
            "_subject_id": binding_subject_id,
        }

    output_subjects: dict[str, Any] = {}
    for subject_id in scope_subjects:
        output_subjects[subject_id] = {
            "title": catalog_subjects[subject_id]["title"],
            "category": catalog_subjects[subject_id]["category"],
            "requirement_strength": catalog_subjects[subject_id]["requirement_strength"],
            "statement": scope_subjects[subject_id]["statement"],
        }

    projected_inventory_locator, projected_inventory_identity = _project_inventory_projection(inventory_projection, authority_root)
    _require(projected_inventory_locator == projected_locator, "INVENTORY_LOCATOR_MISMATCH", "/inventory_projection/locator", "inventory_projection locator does not match projected authority root")

    # Convert losses first to build references and renamed identifiers.
    projected_losses: dict[str, Any] = {}
    for loss in losses:
        projected = _project_loss(
            _require_mapping(loss, "LOSS_TYPE", "/losses"),
            tracker,
        )
        if projected is None:
            continue
        loss_id, payload = projected
        _require(loss_id not in projected_losses, "LOSS_ID_DUPLICATE", f"/losses/{loss_id}", "duplicate loss_id after mapping")
        projected_losses[loss_id] = payload

    # Convert catalog exclusions to map entries and add duplicate detection.
    excluded: dict[str, Any] = {}
    for exclusion in reviewed_exclusions:
        exc = _require_mapping(exclusion, "REVIEWED_EXCLUSION_TYPE", "/reviewed_exclusions")
        source_id = _require_non_empty(exc.get("source_id"), "REVIEWED_EXCLUSION_SOURCE_ID_MISSING", "/reviewed_exclusions/source_id", "source_id required")
        _require(SOURCE_ID_RE.fullmatch(source_id) is not None, "REVIEWED_EXCLUSION_SOURCE_ID_INVALID", f"/reviewed_exclusions/{source_id}", "source_id must be source-id pattern")
        _require(source_id not in excluded, "REVIEWED_EXCLUSION_SOURCE_ID_DUPLICATE", f"/reviewed_exclusions/{source_id}", "duplicate reviewed_exclusion source_id")
        reason_code = _require_non_empty(
            exc.get("reason_code"),
            "REVIEWED_EXCLUSION_REASON_MISSING",
            f"/reviewed_exclusions/{source_id}/reason_code",
            "reason_code required",
        )
        _require(
            reason_code in {
                "duplicate",
                "out-of-scope",
                "navigation-only",
                "obsolete",
                "generated-alias",
                "unavailable",
                "other",
            },
            "REVIEWED_EXCLUSION_REASON_INVALID",
            f"/reviewed_exclusions/{source_id}/reason_code",
            "invalid exclusion reason_code",
        )
        title = _require_non_empty(
            exc.get("title"),
            "REVIEWED_EXCLUSION_TITLE_MISSING",
            f"/reviewed_exclusions/{source_id}/title",
            "title required",
        )
        locator = _require_non_empty(
            exc.get("locator"),
            "REVIEWED_EXCLUSION_LOCATOR_MISSING",
            f"/reviewed_exclusions/{source_id}/locator",
            "locator required",
        )
        _require(HTTPS_URL_RE.match(locator) is not None, "REVIEWED_EXCLUSION_LOCATOR_INVALID", f"/reviewed_exclusions/{source_id}/locator", "locator must be https URL")
        rationale = _project_reviewed_exclusion_rationale(
            source_id,
            exc,
            tracker,
        )

        excluded[source_id] = {
            "disposition": "excluded",
            "title": title[:500],
            "source_kind": "other",
            "content": {
                "content_mode": "excluded",
                "locator": locator,
                "inventory_entry_identity": _make_identity(
                    {
                        "source_id": source_id,
                        "title": title,
                        "reason_code": reason_code,
                        "rationale": rationale,
                    }
                ),
            },
            "reason_code": reason_code,
            "rationale": rationale,
        }

    # Validate source ids and duplicate closure across included+excluded.
    seen_source_ids: set[str] = set(excluded)
    for source in sources:
        sid = source.get("source_id") if isinstance(source, dict) else None
        _require(_is_str(sid), "SOURCE_ID_MISSING", "/sources/source_id", "source_id required")
        _require(sid not in seen_source_ids, "SOURCE_ID_DUPLICATE", f"/sources/{sid}", "source_id duplicate with exclusions")
        _require(SOURCE_ID_RE.fullmatch(sid) is not None, "SOURCE_ID_INVALID", f"/sources/{sid}", "source_id must be source-id pattern")
        seen_source_ids.add(sid)

    subject_renames = {
        action.record_id: str(action.replacement_id)
        for action in tracker.actions
        if action.record_type == "subject" and action.action == "rename"
    }
    subject_drop = {
        action.record_id
        for action in tracker.actions
        if action.record_type == "subject" and action.action == "drop"
    }
    loss_renames = {
        action.record_id: str(action.replacement_id)
        for action in tracker.actions
        if action.record_type == "loss" and action.action == "rename"
    }
    loss_drop = {
        action.record_id
        for action in tracker.actions
        if action.record_type == "loss" and action.action == "drop"
    }
    projected_sources, selector_losses, has_json_pointer = _project_sources(
        sources,
        subject_renames,
        subject_drop,
        loss_renames,
        loss_drop,
        valid_subjects=set(scope_subjects),
        valid_losses=set(projected_losses),
        catalog_wide_binding=catalog_wide_binding,
    )

    projected_sources.update(excluded)

    # subject and loss closure checks (bidirectional)
    for source_id, source_payload in projected_sources.items():
        if source_payload["disposition"] != "included":
            continue
        _require(source_payload["subject_ids"], "SOURCE_SUBJECTS_EMPTY", f"/discovered_sources/{source_id}/subject_ids", "included source must have subject bindings")
        selector_subject_union: set[str] = set()
        for selector in source_payload["selectors"]:
            selector_subject_union.update(selector["subject_ids"])
        _require(
            selector_subject_union == set(source_payload["subject_ids"]),
            "SOURCE_SUBJECT_CLOSURE_MISMATCH",
            f"/discovered_sources/{source_id}/subject_ids",
            "source.subject_ids must equal selector subject closure",
        )
        for selector in source_payload["selectors"]:
            for lid in selector["loss_ids"]:
                _require(lid in projected_losses, "SOURCE_SELECTOR_LOSS_MISSING", f"/discovered_sources/{source_id}/selectors/{selector['selector_id']}/loss_ids", "selector loss_id missing")
        for lid in source_payload["loss_ids"]:
            _require(lid in projected_losses, "SOURCE_LOSS_MISSING", f"/discovered_sources/{source_id}/loss_ids/{lid}", "source loss_id not projected")

    # All scope-bound subject refs in losses must also exist as declared subjects.
    for loss_payload in projected_losses.values():
        for source_ref in loss_payload["affected_source_ids"]:
            _require(source_ref in projected_sources, "LOSS_AFFECTED_SOURCE_MISSING", "/losses/affected_source_ids", "loss references missing source")
            _require(loss_payload["affected_source_ids"].count(source_ref) == 1, "LOSS_AFFECTED_SOURCE_DUPLICATE", "/losses/affected_source_ids", "affected_source_ids contains duplicates")

    # selector/loss ids referenced by any source must exist and duplicate closure is an error by construction.
    for lid in selector_losses:
        _require(lid in projected_losses, "LOSS_REFERENCE_MISSING", "/losses", "loss references required by selectors must exist")

    out_limitations: list[str] = []
    for index, item in enumerate(limitations):
        if not _is_str(item):
            continue
        action = tracker.consume_limitation(
            str(item),
            f"/limitations/{index}",
        )
        if action is not None and action.action == "drop":
            continue
        value = (
            action.replacement_text
            if action is not None and action.action == "rewrite"
            else item
        )
        _require(
            _is_str(value) and str(value).strip() != "",
            "LEGACY_LEDGER_REPLACEMENT_TEXT_INVALID",
            f"/limitations/{index}",
            "mapped limitation text must be non-empty",
        )
        out_limitations.append(_normalize_text(value))
    if has_json_pointer:
        if LIMITATION_CLEAN_TEXT not in out_limitations:
            out_limitations.append(LIMITATION_CLEAN_TEXT)
    if MIGRATION_INVENTORY_LIMITATION not in out_limitations:
        out_limitations.append(MIGRATION_INVENTORY_LIMITATION)

    inventory_identity = _safe_copy(projected_inventory_identity)
    projected_snapshot_identity: dict[str, Any] | None = None

    if version_scope["kind"] == "latest-at-retrieval":
        projected_snapshot_identity = _snapshot_from_sources_and_exclusions(projected_sources)
        version_scope["snapshot_identity"] = projected_snapshot_identity
    if version_scope["kind"] != "latest-at-retrieval":
        version_scope["snapshot_identity"] = None
        version_scope["retrieved_utc"] = None

    projected_authority_revision = _project_authority_revision(
        input_catalog.get("authority_revision"),
        version_scope["kind"],
        projected_inventory_identity,
        projected_snapshot_identity,
    )

    discovered_sources_payload = canonical_projection_bytes({sid: projected_sources[sid] for sid in sorted(projected_sources)})
    discovery_processor = {
        "processor_id": "official-document-source-catalog-migrator",
        "processor_version": "2026.07",
        "assurance_mode": "unverified",
        "implementation_ref": None,
        "configuration_ref": None,
        "dependency_lock_ref": None,
        "input_sha256": inventory_identity["sha256"],
        "output_sha256": _sha256_hex(discovered_sources_payload),
        "attestation_id": None,
        "deterministic": True,
    }

    output: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "authority_id": authority_id,
        "provider_id": provider_id,
        "authority_root": authority_root,
        "version_scope": version_scope,
        "authority_revision": projected_authority_revision,
        "upstream_universe_complete": bool(input_catalog["upstream_universe_complete"]),
        "inventory_locator": projected_inventory_locator,
        "inventory_identity": inventory_identity,
        "discovery_processor": discovery_processor,
        "discovered_sources": {sid: projected_sources[sid] for sid in sorted(projected_sources)},
        "subjects": output_subjects,
        "losses": projected_losses,
        "limitations": out_limitations,
        "blockers": _project_blockers(blockers, tracker),
    }

    tracker.verify_complete()
    _require(output["authority_revision"] != "", "AUTHORITY_REVISION_MISSING", "/authority_revision", "authority_revision cannot be empty")
    return output
