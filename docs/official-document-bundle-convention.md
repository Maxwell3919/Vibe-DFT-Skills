# Official-Document Coverage Bundle Convention

## Scope

Every source-backed Skill in `registry/skill-registry.yaml` participates in
official-document coverage discovery. This includes `active` and `development`
entries with the canonical path `skills/<skill-id>`. Planned entries have no
source path and are not discoverable bundles.

Discovery and semantic assurance are separate gates:

- `tools/validate_official_document_bundles.py` discovers packs and validates
  their registration boundary;
- `tools/validate_official_document_coverage.py` validates the five
  official-document contract families and their cross-record semantics.

The discovery tool invokes the semantic validator as a black-box CLI. It does
not reimplement the five contract schemas. Discovery additionally checks the
discovery-owned `skill_id` binding in the scope and coverage records so copied
records cannot satisfy a different Skill. Changes to other contract fields do
not silently change the discovery convention.

## Fixed entrypoint

The only canonical entrypoint for one Skill is:

```text
skills/<skill-id>/references/official-source-pack/bundle.json
```

The registration record has this exact shape:

```json
{
  "bundle_type": "official-document-coverage",
  "schema_version": "1.0",
  "skill_id": "example-skill",
  "records": {
    "corpora": ["corpus.json"],
    "slice_manifests": ["slices.json"],
    "license_reviews": ["license-review.json"],
    "scope_inventory": "scope-inventory.json",
    "coverage": "coverage.json"
  }
}
```

`corpora`, `slice_manifests`, and `license_reviews` are nonempty lists.
`scope_inventory` and `coverage` identify one record each. A pack may use
multiple corpus, slice, or license-review records by adding paths to the
corresponding list.

Every path is a canonical relative POSIX path below the pack directory.
Absolute paths, `.` or `..` segments, backslashes, duplicate registrations,
symlinks, hard links, and special files are forbidden. Every file in the pack
other than `bundle.json` must appear exactly once in `records`. A registered
file that is absent and a present file that is not registered are both
invalid. Supporting inventories or source artifacts belong outside this
registration pack and must be content-bound from the contract records; an
arbitrary path-only supporting-file lane is intentionally not available.

This is a repository-local discovery registration, not the portable immutable
`bundle-manifest@1.0` artifact format. Exact content identity, source
authority, license/storage rules, scope inventory, loss accounting, and claim
coverage remain the semantic validator's responsibility.

## Independent hash domains

The canonical Skill `source_tree_sha256` binds every ordinary file below the
registered Skill path except exactly:

```text
references/official-source-pack/**
```

No other generated, hidden, reference, or documentation directory is excluded.
This single exclusion prevents a fixed-point loop: scope and coverage records
inside the pack may bind `source_tree_sha256`, while updating those records
does not change the hash they bind. The scope validator uses the same
`skill_registry.source_tree_digest()` file enumeration, so a deterministic
exact-tree inventory must include every non-pack Skill file and must not
include pack records.

The exclusion is not a trust exemption. Pack bytes are independently protected
by exact registration closure, record hashes, the five official-document
contracts, the semantic coverage validator, migration monotonicity, and the
strict release gate. A malformed, unregistered, partial, or missing required
pack still fails according to the status rules below.

The exact same path is also excluded from the legacy tracked-storage namespace:

```text
skills/<skill-id>/references/official-source-pack/**
```

This is an independent policy domain, not a general `official-*` exclusion.
`official-source-pack-copy/`, a sibling `official-*` directory, or any other
near-match remains in the closed legacy-storage audit. Pack metadata and
content are governed by registration closure plus the corpus, slice, license,
scope, and coverage contracts. Legacy mirrors and indexes outside the exact
pack path remain governed by
`registry/official-document-storage-discovery.yaml`.

## Temporary migration ledger

`registry/official-document-bundle-expectations.yaml` is a canonical,
exact-set registry for every source-backed Skill. Each entry has one state:

- `legacy-missing`: no pack may be present yet; normal audit reports `missing`;
- `pack-required`: the canonical pack must be present and valid.

The first real pack and the transition from `legacy-missing` to
`pack-required` must land atomically. A present pack cannot be hidden behind
`legacy-missing`, and `pack-required` can never downgrade. A newly introduced
source-backed Skill must enter with `pack-required` and a real pack in the same
change.

Current-tree exactness alone cannot prove that a pack was not deleted in the
same change. `--baseline-ref <commit>` therefore compares the candidate with a
trusted Git baseline and rejects pack deletion, expectation downgrade, or a
new source-backed Skill without its required pack. The first reviewed commit
that introduces the ledger is a bounded bootstrap; later commits always have a
real ledger baseline.

## Result states

Repository discovery reports one state per source-backed Skill:

| State | Meaning | Normal audit | Strict release |
|---|---|---:|---:|
| `complete` | Registration is valid and the semantic validator exits 0 | pass | pass |
| `partial` | Registration and semantics are valid, but assurance is below `complete` and the semantic validator exits 3 | pass with explicit blocker | exit 3 |
| `missing` | A source-backed Skill has no pack directory | pass with explicit blocker | exit 3 |
| `invalid` | Registry, registration, path safety, file closure, or semantic validation failed | exit 2 | exit 2 |

If `official-source-pack/` exists without `bundle.json`, the result is
`invalid`, not `missing`. A pack under a Skill that has no source-backed
registry record is also `invalid`. These rules prevent malformed or
unregistered bundles from disappearing behind legacy migration status.

Normal audit mode intentionally does not claim release completeness. During
migration it keeps ordinary development tests runnable while printing every
missing or partial release blocker. A newly added source-backed Skill is not a
new legacy exception: it must arrive with a required pack. There is no
grandfather allowlist. Strict release mode accepts only a repository in which
every source-backed Skill is `complete`.

## Commands and CI

Run the discovery layer directly:

```text
python3 tools/validate_official_document_bundles.py
python3 tools/validate_official_document_bundles.py --baseline-ref <trusted-base-ref>
python3 tools/validate_official_document_bundles.py --strict-release
```

The normal repository validator includes report mode:

```text
python3 tools/validate_all_skills.py --baseline-ref <trusted-base-ref>
```

Release candidates must use:

```text
python3 tools/validate_all_skills.py --strict-release --baseline-ref <trusted-base-ref>
```

CI fetches complete Git history and always supplies a migration baseline. Pull
requests use `github.event.pull_request.base.sha`; ordinary pushes use
`github.event.before`. A new ref with an all-zero `before` uses `HEAD^` only
when it resolves; a root commit without a trustworthy baseline fails closed.
Force-push comparison remains against the event's prior head rather than
silently comparing with the candidate itself.

Pull requests and ordinary branch pushes use report mode. Every pushed tag is
treated as a release attempt and uses strict mode in the same validation
invocation, avoiding a duplicate semantic pass. Missing or valid-but-partial
packs remain visible release blockers without preventing ordinary migration
branches from running their test suite. Post-push tag CI does not replace the
mandatory fresh pre-tag command or external tag-protection policy.

Running without `--baseline-ref` performs only a current-state audit. It cannot
support a migration-monotonicity claim.

Neither mode establishes native software availability, calculation
correctness, numerical convergence, physical validity, or scientific
acceptance.
