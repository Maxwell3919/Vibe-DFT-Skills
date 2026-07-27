# Local official-manual Markdown cache

Use the repository-wide cache tool before relying on an external official document body that is not already present in this Skill. The tool accepts only registered HTTPS authorities, verifies pinned byte receipts, converts HTML with the repository-pinned `helloworld-Co/html2md`, preserves non-HTML source text losslessly, and writes third-party bodies outside Git.

From the repository root:

```bash
python3 tools/sync_official_manual_cache.py --refresh --skill cif-structure-analysis
python3 tools/sync_official_manual_cache.py --check
```


If a mutable official page has changed since its registered receipt, `--allow-live-drift` may be used to create a readable local copy only. The result is labeled `blocked-for-version-sensitive-use-until-registry-refresh`; never cite it as a receipt-verified versioned source.

Read the generated `index.md` under `${XDG_CACHE_HOME:-$HOME/.cache}/vibe-dft-skills/official-manuals/cif-structure-analysis/`. Keep the official URL, authority/version identity, and local conversion label in every claim. A cache pass proves document identity and readability only; it does not prove executable behavior, convergence, or physical validity.

This Skill has 10 registered source records across these authorities:

- `ase-release-source-docs-3-29-0`
- `gemmi-0-7-5-source-docs`
- `iucr-comcifs-cif-standards`
- `pycifrw-5-0-1-source-docs`
- `spglib-release-source-docs-2-7-0`
