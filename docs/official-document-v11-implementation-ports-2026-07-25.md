# Official-document v1.1 implementation ports

Date: 2026-07-25
Base commit: `66f5affcc4c6bd1c9c11c13304b5e280f1ee98dd`
Implementation branch: `codex/official-doc-v11-migration`

## Purpose

This document freezes the implementation boundary for the atomic migration
from the wave-0 five-family official-document pack to the policy-free v1.1
technical protocol. It is an execution handoff, not a completeness or release
claim.

Code changes are assigned only through explicitly bounded implementation
ports. Each port has one file owner, defined inputs and outputs, and focused
acceptance commands. A port must not edit files owned by another port.

## Frozen protocol boundary

The four v1.1 technical contracts are:

- `official-document-source-catalog@1.1`;
- `official-corpus-manifest@1.1`;
- `document-slice-manifest@1.1`;
- `skill-document-coverage@1.1`.

The generated semantic record families are:

- corpus manifests;
- slice manifests;
- the existing technical scope inventory;
- coverage records.

`bundle.json` remains an exact record index rather than a semantic record.
The existing seed and scope-inventory contracts remain supporting control
interfaces unless a separately reviewed contract change is made. All 26 seeds
must still be enumerated, hash-checked, and refreshed when their referenced
bytes change.

The production writer, validator, bundle discovery, dashboard, portable
distribution, registries, processor lock, declarative inputs, and generated
packs must not depend on `official-source-license-review`,
`license_review_refs`, `license_reviews`, or a `license-review-*` file.
Content placement is validated as technical topology:

- `metadata-only`;
- `external-content`;
- `embedded-content`;
- `excluded`.

The technical path validates safe relative paths, regular-file identity,
hashes, byte sizes, byte-range closure, deterministic transformation receipts,
source provenance, scope totality, and coverage mappings. It does not make a
license or legal judgment.

Independent credential, privacy, private-path, restricted-potential, archive,
opaque-binary, runtime-output, lifecycle, route, side-effect, and scientific
claim gates remain in force.

## Current and target topology

The wave-0 checkpoint contains 26 packs and 249 JSON files:

| Family | Current | Target |
|---|---:|---:|
| Corpus manifests | 57 | 57 |
| Slice manifests | 57 | 57 |
| License-review records | 57 | 0 |
| Scope inventories | 26 | 26 |
| Coverage records | 26 | 26 |
| Bundle indexes | 26 | 26 |
| Total | 249 | 192 |

The input graph contains 26 seeds and 57 provider inputs:

- 55 `declarative-catalog-v1` inputs;
- one QE manifest adapter input;
- one VASP Wiki manifest adapter input.

Removing the fifth record family must not change `scope_complete` from false
or raise a pack, Skill, route, interface, or scientific assurance status.

## Implementation ports

### CI-01 — clean-worktree regression

Interface:

- Input: a clean checkout where
  `audit_repository(ROOT).worktree_drift_findings == ()`.
- Output: a stable live-repository test that remains release-blocked by the
  2,075 legacy artifacts.

Exclusive file:

- `tests/test_official_document_storage_gate.py`

Requirements:

- Replace the dirty-worktree count assumption with the clean invariant.
- Preserve `forbidden_path_count == 2075`.
- Preserve strict-release exit `3`.
- Preserve the deterministic temporary-directory drift test.
- Do not change production storage-gate code.

Acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_official_document_storage_gate
git diff --check -- tests/test_official_document_storage_gate.py
```

### B-01 — writer and neutral technical projection

Interface:

- Input: migrated source catalogs, canonical seeds, scope catalogs, the frozen
  registry snapshot, and the processor lock.
- Output: deterministic corpus, slice, scope, coverage, and bundle bytes with
  no fifth record family.

Exclusive files:

- `tools/build_official_document_packs.py`
- `tests/test_official_document_pack_builder.py`

Requirements:

- Consume the v1.1 source-catalog tagged maps.
- Emit v1.1 corpus, slice, and coverage records.
- Preserve the existing technical scope inventory.
- Remove license projection, record generation, refs, output names, and
  semantic-validator arguments.
- Preserve command-wide staging, `fsync`, exact inventory validation, atomic
  directory swap, rollback, and conflict tombstones.
- Do not edit catalogs, seeds, registries, the processor lock, or generated
  packs.

Acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_official_document_pack_builder
```

### B-02 — canonical four-record semantic validator

Interface:

- Input: corpus manifests, slice manifests, one scope inventory, and one
  coverage record.
- Output: deterministic findings and assurance status for the technical
  four-record closure.

Exclusive files:

- `tools/validate_official_document_coverage.py`
- `tests/test_official_document_coverage.py`

Requirements:

- Use exact v1.1 selectors for corpus, slice, and coverage.
- Preserve authority/provider binding, exact record hashes, discovered-source
  partition, corpus-to-slice identity, byte ranges, loss accounting, scope
  totality, mapping closure, processor identity, and status ceilings.
- Remove `license_review_paths`, `--license-review`, license trust, terms,
  reviewer, obligation, expiry, and redistribution decisions.
- Reject mixed v1.0/v1.1 records and obsolete fifth-family inputs.
- Keep `scope_complete == false` assurance-capped.

Acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_official_document_coverage
```

### B-03 — bundle discovery and dashboard

Interface:

- Input: exact four-family bundle registrations and validator results.
- Output: fail-closed discovery plus a technical dashboard projection.

Exclusive files:

- `tools/validate_official_document_bundles.py`
- `tools/build_official_document_dashboard.py`
- `tests/test_official_document_bundle_discovery.py`
- `tests/test_official_document_dashboard.py`
- `docs/official-document-bundle-convention.md`

Requirements:

- Register exactly `corpora`, `slice_manifests`, `scope_inventory`, and
  `coverage`.
- Reject missing, extra, orphaned, mixed-version, hardlink-swapped, or
  unregistered records.
- Remove the license-review CLI bridge and TOCTOU snapshot family.
- Read the v1.1 coverage status object.
- Do not alias a license status into a storage status.

Acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_official_document_bundle_discovery \
  tests.test_official_document_dashboard
```

### B-04 — active-only portable distribution

Interface:

- Input: the active-only source tree and canonical v1.1 packs.
- Output: a deterministic portable archive whose four-family packs replay the
  canonical semantic validator.

Exclusive files:

- `tools/build_active_only_distribution.py`
- `tests/test_active_only_distribution.py`

Requirements:

- Change `PACK_RECORD_FAMILIES` to the four-family profile.
- Remove license-review refs and duplicated license-ceiling logic.
- Preserve source selection, transformed-output, archive-member, and
  extracted-tree content scans.
- Preserve archive path, hash, size, hardlink, symlink, and nested-archive
  fail-closed behavior.

Acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_active_only_distribution
```

### B-05 — interface registration and governance ownership

Interface:

- Input: the frozen v1.1 schemas and the production writer/validator profile.
- Output: exact active interface registrations, schema hashes, and production
  ownership.

Exclusive files:

- `registry/interface-registry.yaml`
- `tests/test_official_document_v11_contracts.py`
- `tests/test_wave0_governance.py`
- `tests/test_bundle_validation.py`
- `tests/test_contract_catalog.py`

Requirements:

- Register the four v1.1 technical interfaces by exact version.
- Remove the obsolete license-review interface from the production profile.
- Keep unversioned resolution ambiguous when multiple versions exist.
- Give each active semantic obligation exactly one production owner.
- Do not change Skill lifecycle, installability, routability, or side-effect
  classes.

Acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v \
  tests.test_official_document_v11_contracts \
  tests.test_wave0_governance \
  tests.test_bundle_validation \
  tests.test_contract_catalog
PYTHONDONTWRITEBYTECODE=1 python3 tools/interface_registry.py
```

### B-06 — declarative inputs, hashes, and generated integration

Interface:

- Input: final B-01 through B-05 bytes and the 26 canonical seeds.
- Output: migrated declarative inputs, refreshed hashes and lock, and 26
  canonical packs containing exactly 192 JSON files.

Exclusive ownership:

- the 55 declarative provider catalogs enumerated from the 26 seeds;
- the 26 `source-pack-seed.json` files;
- deterministic Skill-local catalog/seed writers;
- Skill-local tests and maintenance validators that parse the migrated
  catalogs or seeds, including their schema-version, tagged-map, and removed
  fifth-family assertions;
- scope catalogs whose origin hashes change;
- `contracts/official-document-pack-builder-lock.json`;
- `registry/skill-registry.yaml`;
- `registry/official-document-consumers.yaml`;
- `registry/official-document-bundle-expectations.yaml`;
- final affected central registry hashes other than
  `registry/interface-registry.yaml`, which remains exclusively owned by
  B-05;
- all `skills/*/references/official-source-pack/**`.

Requirements:

- Enumerate catalogs through seed refs, not filename globs.
- Convert included and excluded sources to the v1.1 tagged-map topology without
  losing selectors, receipts, subjects, statements, or loss records.
- Delete the top-level catalog license object rather than translating it into
  a technical content mode.
- Derive technical content modes from actual locator, identity, receipt, and
  content placement evidence.
- Refresh seed, scope, source-tree, processor, consumer, and bundle hashes
  from final bytes. B-05 alone refreshes interface registrations and their
  schema hashes.
- Generate all packs once, then require a second byte-clean `--all --check`.
- Do not hand-edit generated pack JSON.

Focused acceptance:

```text
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_official_document_packs.py --all
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_official_document_packs.py \
  --all --check
```

Expected generated closure:

```text
packs=26
providers=57
corpora=57
slice_manifests=57
scope_inventories=26
coverage_records=26
bundle_indexes=26
license_review_records=0
json_total=192
```

## Sequencing and integration boundary

1. Complete CI-01 independently.
2. Freeze B-05 interface identities and the B-02 validator call shape.
3. Implement B-01 and B-02 without touching shared hashes or generated packs.
4. Implement B-03 and B-04 against the frozen validator interface.
5. Run B-06 as the sole data, hash, lock, non-interface registry-projection,
   and generated-pack integration owner. B-05 remains the sole
   `interface-registry.yaml` owner.
6. Review the combined diff before any full-suite claim.
7. Run focused tests, then the complete pre-commit repository verification.
8. Commit only the reviewed and verified migration tree.
9. Confirm the committed worktree is clean, then build and verify the fresh
   active-only archive with `--require-clean-commit`.
10. Publish without force-pushing.

The pack-directory swap is atomic only for generated pack directories. The
repository-level migration is made reviewable and recoverable through the
implementation branch and a single coherent Git checkpoint.

## Live implementation status

This section records the live handoff state on 2026-07-25. It supersedes any
earlier note that the requested worker model was unavailable, but it does not
change the acceptance boundary above.

| Port | Live state | Evidence boundary |
|---|---|---|
| CI-01 | complete | the clean-worktree invariant and the 2,075-artifact strict-release block remain separate |
| B-01 | complete | the writer emits only corpus, slice, scope, coverage, and the exact bundle index |
| B-02 | complete | the validator consumes the four-record v1.1 closure and rejects obsolete fifth-family inputs |
| B-03 | complete | bundle discovery and dashboard use the exact four-family profile |
| B-04 | complete | portable distribution verifies the v1.1 source identity and external receipt contract |
| B-05 | complete | active production interfaces and schema hashes select v1.1; obsolete interfaces are non-routable tombstones |
| B-06 | integrated pending final repository acceptance | all 55 declarative catalogs are v1.1; 26 packs contain 192 JSON files and no license-review records |

The official-document production call graph now projects authority, version,
locator, content identity, and transformation receipts without consuming
`license_policy`, `redistribution_policy`, `license_trust`, or
`bundle_content_policy`. The fifth record family and its references are absent
from generated packs, the active consumer profile, bundle discovery, dashboard,
coverage validation, and portable distribution.

This boundary does not claim that every historical compatibility fixture,
environment profile, or unrelated legacy bundle validator in the repository
contains no policy vocabulary. Those components do not enter the v1.1
four-record production call graph and are outside this atomic migration.
Future cleanup must be separately reviewed rather than mixed into this
release checkpoint.

The B-06 transaction converted and schema-validated 55/55 seed-enumerated
declarative catalogs, preserved the specialized QE and VASP manifest adapters,
refreshed all dependent seeds and identities, and regenerated all 26 packs.
The migration used an exact typed ledger with exact consumption counts, not a
keyword classifier.

All source-backed Skill maintenance entrypoints reviewed in this closeout now
emit or validate the checked-in v1.1 catalog shape. CIF, CP2K,
`dft-campaign-efficiency`, `dft-postprocess`, SIESTA, and ML intentionally
construct an exact typed v1.0 preimage before the shared converter produces
their canonical v1.1 output.

## Pre-commit repository acceptance

```text
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_development_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_all_skills.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_repository.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_official_document_packs.py \
  --all --check
PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_hygiene.py --include-ignored
git diff --check -- . \
  ':(exclude)skills/qe-rigorous-calculations/references/official-*'
git status --short --branch
```

Earlier failing WIP results remain historical diagnosis only. A fresh
working-tree `tools/run_tests.py` run completed 836 core tests with one skip
and all 33 deterministic active-Skill commands after the stale Skill-local
v1.0 maintenance tests were migrated. The remaining local acceptance commands
in the sequence above also completed successfully, including 60 deterministic
development-Skill commands, the 26-pack byte check, repository audit, and
hygiene audit. The clean-commit archive and GitHub checks must still finish
successfully before publication; their results must not be inferred from the
working-tree checks.

After the reviewed tree is committed, the release candidate must additionally
build and verify a fresh active-only archive in a new empty extraction
directory. `--require-clean-commit` deliberately cannot pass before that
commit because it binds every selected byte and executable mode to `HEAD`.
Strict release remains blocked while legacy storage findings, incomplete
scope, invalid packs, dirty index or worktree state, lifecycle violations, or
privacy/content-policy findings remain.

The post-commit archive CLI uses a positional archive argument for `verify`:

```text
release_archive_dir="$(mktemp -d)"
release_extract_dir="$(mktemp -d)"
PYTHONDONTWRITEBYTECODE=1 python3 \
  tools/build_active_only_distribution.py build \
  --root . \
  --output "$release_archive_dir/active-only.tar" \
  --require-clean-commit
PYTHONDONTWRITEBYTECODE=1 python3 \
  tools/build_active_only_distribution.py verify \
  "$release_archive_dir/active-only.tar" \
  --extract-to "$release_extract_dir"
```

Passing these repository checks does not establish software availability,
calculation completion, numerical convergence, physical validity, or a
scientific result.

## Closeout boundary

The user explicitly authorized `gpt-5.6-sol` to finish the bounded code ports
after the Spark allocation was exhausted. Each worker received explicit file
ownership, inputs, outputs, forbidden areas, and focused acceptance commands.
No worker committed, pushed, or merged independently.

The generated coverage state remains evidence-bounded:

- 5 packs are `partial`;
- 21 packs are `blocked`;
- 0 packs are `complete`.

Therefore this checkpoint closes the protocol, generator, migration, and
audit-chain implementation. It does not claim that all upstream official
documentation has been completely split or covered. Upstream additions and
reviewed exclusions remain ordinary future coverage work.

The integration owner obtained fresh successful exits from the complete
pre-commit sequence on this working tree. The remaining publication steps are
to commit only the reviewed task files, verify a clean-commit active-only
archive, pass GitHub CI, merge the stacked pull requests without force-pushing,
and revalidate the local installed Skill links against the merged `main`.
