# Official-document wave 0 handoff

Date: 2026-07-24
Branch: `codex/official-doc-completeness-wave0`
Repository: `Maxwell3919/Vibe-DFT-Skills`

## Checkpoint purpose

This branch is a reviewable wave-0 checkpoint, not a claim that every official
document body is already stored and fully segmented. It establishes the
authority, source-universe, source-identity, slice, scope, coverage, storage,
drift, and active-only distribution controls needed for a later atomic content
migration.

## Included work

- A central authority and consumer-binding model for official sources.
- Deterministic source-pack seeds, catalogs, builder, semantic validator,
  bundle discovery, storage audit, dashboard, and drift checks.
- Canonical source packs for 26 source-backed Skills and 57 provider inputs.
- Development-Skill test discovery and CI wiring.
- Independent active-only distribution checks using one shared
  `release_content_policy` implementation at source selection, transformed
  output, archive creation, extraction, and unpacked-tree verification.
- A read-only materialization preflight:
  `official_document_materialization.evaluate_request(request, import_root)`.
  It has no network access or write side effects, returns only exit `0` or `2`,
  and proposes content-addressed bytes entirely in memory.
- Four policy-free v1.1 technical contracts for source catalog, corpus,
  slices, and coverage. These contracts are intentionally present as the next
  migration interface and are not yet wired into the production builder.
- Repository-audit entrypoints set `sys.dont_write_bytecode = True` before
  importing local modules, preventing their own cache output from polluting a
  hygiene run.

## Snapshot and evidence boundary

The wave-0 inventory contains:

- 26 source-backed Skills;
- 57 provider inputs;
- 3,421 discovered source entries;
- 462 included entries and 2,959 reviewed exclusions;
- 1,586 deterministic slices.

All current generated slices are metadata-only/external. No third-party
official-document body was silently added by this branch. Therefore these
counts prove inventory and segmentation metadata closure, not local body
completeness.

The storage audit also identifies 2,075 legacy official artifacts totaling
13,412,851 bytes as release blockers. They must not be promoted merely because
the new pack metadata validates.

## Fresh checkpoint verification

The following release checks were run from this worktree on 2026-07-24 with
`PYTHONDONTWRITEBYTECODE=1` where applicable:

- `python3 tools/run_tests.py`: exit `0`; 865 root tests passed, followed by
  all 33 deterministic active-Skill maintenance commands.
- `python3 tools/run_development_tests.py`: exit `0`; 19 source-backed
  development Skills completed 60 deterministic maintenance commands, with
  zero skipped.
- `python3 tools/validate_all_skills.py`: exit `0`; 26 Skills validated and 26
  official-document bundles audited in report mode. The summary remains
  `complete=0 partial=26 missing=0 invalid=0`; this is intentionally not a
  release-completeness claim.
- `python3 tools/audit_repository.py`: exit `0`; interfaces aligned across
  4 calculation codes, 7 active Skills, and 19 development Skills.
- `python3 tools/build_official_document_packs.py --all --check`: exit `0`;
  all 26 deterministic packs matched their generated state.
- `git diff --check -- .
  ':(exclude)skills/qe-rigorous-calculations/references/official-*'`: exit `0`.
- `python3 tools/audit_hygiene.py --include-ignored`: exit `0`; repository
  hygiene clean.

During verification, the first root-suite run exposed one version-selection
ambiguity after adding the parallel v1.1 contracts. The governance test now
resolves the exact registered interface identifier rather than an unversioned
contract kind; the targeted regression and the complete 865-test rerun both
passed.

## Deliberately deferred

1. The current production builder, semantic validator, registries, and
   generated packs still use the wave-0 v1.0 five-record protocol. The new
   v1.1 four-record contracts are interface-only at this checkpoint.
2. The v1.1 builder migration must remain atomic. Its target inventory is
   57 corpus records, 57 slice manifests, 26 scope inventories, 26 coverage
   records, and 26 bundle indexes: 192 JSON files in total.
3. The migration must update the 55 declarative catalogs, all 26 seeds,
   source-tree hashes, processor locks, registry projections, and all generated
   packs in one transaction.
4. `scope_complete` remains false. Removing an obsolete record family must not
   raise an assurance status to complete without new scope-completeness
   evidence.
5. A repository-wide release scanner draft was not shipped. Review found three
   unresolved P1 issues: one historical blob can have multiple policy-relevant
   paths, Git subprocess output needs a true streaming hard bound, and
   shallow/partial history must never be reported as complete. The shared
   content rules remain shipped only through the verified active-only path.

## Next atomic change

Perform the following as one reviewed migration:

1. Make the v1.1 four-record protocol the only accepted writer and validator
   profile.
2. Migrate the 55 declarative catalogs and 26 seeds to the neutral storage
   modes `metadata-only`, `external-content`, `embedded-content`, and
   `excluded`.
3. Remove the obsolete fifth generated record family and every status,
   dashboard, registry, CLI, and hash dependency on it.
4. Recompute catalog refs, the 26 Skill source-tree hashes, processor/runtime
   locks, consumer projections, and interface registrations from final bytes.
5. Regenerate all 26 packs through the existing
   stage-validate-atomic-directory-swap transaction.
6. Run the full verification sequence below and confirm a second
   `build_official_document_packs.py --all --check` is byte-clean.

Content placement is a caller-selected technical topology. The library should
validate only safe paths, regular-file identity, exact hashes and sizes,
source provenance, byte-range closure, and deterministic transformation
receipts.

## Verification and continuation commands

Run from the repository root:

```text
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_development_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_all_skills.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/audit_repository.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_official_document_packs.py --all --check
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_active_only_distribution.py build --root . --output <new-archive.tar>
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_active_only_distribution.py verify --archive <archive.tar> --extract-to <new-empty-directory>
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

Do not infer scientific validity, execution completion, numerical convergence,
or Skill promotion from these repository checks.
