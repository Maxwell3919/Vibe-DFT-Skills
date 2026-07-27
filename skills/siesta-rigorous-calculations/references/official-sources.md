# Official SIESTA source policy

## Pinned evidence boundary

The automated parameter/source set is pinned to official SIESTA tag `5.4.2`, commit `e486d12067b96ff688179f0496d0ec21b6fae0ab`.

- Versioned 5.4 manual: `https://docs.siesta-project.org/projects/siesta/en/5.4/reference/siesta.html`
- Official first-encounter tutorial: `https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/first-encounter/index.html`
- Official utility manual index: `https://docs.siesta-project.org/projects/siesta/en/latest/reference/`
- Official band tutorial: `https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/electronic-structure-analysis/bands/index.html`
- Official DOS tutorial: `https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/electronic-structure-analysis/dos/index.html`
- Official phonon tutorial index: `https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/vibrational-properties/index.html`
- Documentation landing page: `https://siesta-project.org/siesta/Documentation/`
- Official repository/tags: `https://gitlab.com/siesta-project/siesta`
- Pseudopotential landing page: `https://siesta-project.org/siesta/Documentation/Pseudopotentials/`

`manual-cache-receipts/fdf-index.json` is mechanically generated from 47 hash-pinned official manual source files and contains 572 active FDF definitions. Each record preserves label, normalized lookup key, value type, documented default text, macro class, source file/line, and commit-pinned URL. `manual-cache-receipts/source-supplements.json` separately records source-observed behavior absent from manual FDF macros, including `GeometryMustConverge` and parser anchors. Never relabel a source supplement as manual documentation.

The manual's `DOS.kgrid.?`, `PDOS.kgrid.?`, and `LDOS.kgrid.?` entries are
families, not arbitrary wildcards. The deterministic resolver accepts only the
reviewed `MonkhorstPack`, `Cutoff`, and `File` variants and blocks every other
suffix.

## Version and retrieval gates

1. Require an explicit plan/executable version.
2. In run mode, read the unique `Siesta Version` header and require exact normalized equality.
3. Require the plan documentation line and pinned index version to agree.
4. Do not project 5.4 defaults, aliases, PSML behavior, or output grammar onto 4.x/5.2 without a matching evidence set.
5. Treat `stable`/`latest` as unresolved until its concrete version is recorded.

Offline exact-label lookup proves only a pinned local record exists and returns exit 3. With `--live-check`, exact parameter lookup retrieves the record's source file from the pinned GitLab commit and compares the stored full-file hash. Topic routing checks page reachability but does not prove a parameter default.

## Regeneration

Use an official checkout at the exact pinned commit:

```bash
python3 scripts/sync_official_parameters.py \
  --source-tree /authorized/siesta-5.4.2 \
  --expected-commit e486d12067b96ff688179f0496d0ec21b6fae0ab \
  --out references/manual-cache-receipts/fdf-index.json
```

Then exact-check it:

```bash
python3 scripts/sync_official_parameters.py --check \
  --source-tree /authorized/siesta-5.4.2 \
  --out references/manual-cache-receipts/fdf-index.json
```

Do not manually edit the generated index. Multiple official definitions sharing a normalized key remain explicitly ambiguous; `MM.Cutoff` is blocked until its context is resolved.

## Scientific boundary

- A documented default is software behavior, not a recommended or converged value.
- A source string is a parser anchor, not evidence that a run succeeded.
- Tutorials and examples can explain workflow but do not replace versioned parameter definitions.
- Issues/merge requests can establish defect history only when the exact released commit relationship is shown.
- Pseudopotential identity/hash does not establish XC suitability, relativistic suitability, or transferability.
