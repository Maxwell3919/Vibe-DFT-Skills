# Official-manual Markdown cache

`tools/sync_official_manual_cache.py` turns the repository's registered
official-document receipts into a local, readable Markdown layer without
changing the central redistribution boundary.

## Trust boundary

- Discovery is limited to active authorities already bound through generated
  `official-source-pack` manifests.
- Every HTTPS source must match the authority's exact origin, path, query, and
  fragment policy.
- Direct bodies are checked against their registered byte count and SHA-256.
- Exact Git documentation-tree inventories are checked against their canonical
  receipt, commit, and per-file Git blob identity.
- Exact official `docs/` trees that lack a registered per-file inventory may be
  read from the commit-pinned provider archive, but every derived page is
  labeled `pinned-archive-body-unregistered` and remains blocked for a
  receipt-verified version-sensitive claim.
- HTML is converted only by the pinned local
  `helloworld-Co/html2md` installation. Markdown stays Markdown. UTF-8 source
  formats that are not HTML are retained losslessly in a labeled Markdown
  fence. Public official PDFs are extracted locally with `pdftotext`. Script,
  style, and noscript bodies are removed before HTML conversion. Valid JSON
  is indented inside a labeled fence without changing the decoded data.
- Exact repository `docs/` trees may be materialized; exact `src/` and package
  code trees remain provenance metadata and are never presented as parameter
  manuals.
- Repository-validated QE, VASP, and CP2K Markdown snapshots are reused instead
  of being replaced by an unpinned live page.
- Publisher literature records that are not software manuals remain metadata
  routes. License-restricted bodies that cannot be fetched through the
  registered HTTPS route also remain metadata-only. The tool does not bypass
  access controls or imply manual coverage.

The cache is local-only. It is not a new official-document bundle, a license
grant, an execution validation, or scientific evidence by itself.

## Receipt drift

The default refresh fails if a live body differs from its registered receipt.
`--allow-live-drift` is only a readability fallback for mutable official pages.
It records both identities and marks the page
`blocked-for-version-sensitive-use-until-registry-refresh`. A calculation may
not use that page for a version-sensitive default, restriction, or interaction
until the registered source has been reviewed and refreshed.

## Commands

```bash
python3 tools/sync_official_manual_cache.py --inventory
python3 tools/sync_official_manual_cache.py --refresh
python3 tools/sync_official_manual_cache.py --check
python3 tools/sync_official_manual_cache.py --check-routing-docs
```

Use `--skill SKILL_ID` for a bounded refresh. The default cache root is
`${XDG_CACHE_HOME:-$HOME/.cache}/vibe-dft-skills/official-manuals`.

## Readability and identity gates

A valid cache has strict UTF-8 Markdown, no Unicode replacement characters,
bounded downloads, a nonempty conversion result, minimum HTML token retention,
retention of non-ASCII letters, and exact output size/SHA-256 entries in
`manifest.json`. Refreshes stage into a new directory and replace the prior
cache only after the complete staged manifest passes. Invisible source control
characters are never silently dropped: known PDF bullet artifacts are rendered
as bullets, page breaks become explicit comments, and unknown controls become
visible `source-control-U+XXXX` markers after the original byte or Git-object
identity has been checked.

The full local refresh verified on 2026-07-26 contains 6,622 Markdown documents
for all 26 source-backed Skills and 45 active authorities (47,281,815 bytes and
808,015 lines). Its manifest and all documents pass strict UTF-8, zero
replacement-character, zero NUL, zero invisible-control-character, and
per-file size/SHA-256 validation.

These gates detect corruption and gross conversion loss. They do not prove
that a manual is complete, current for an unregistered executable version, or
sufficient for a scientific claim. Each Skill's scientific and execution gates
remain authoritative.
