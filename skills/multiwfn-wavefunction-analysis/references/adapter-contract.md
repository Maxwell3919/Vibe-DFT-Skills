# Adapter contract

## Dry-run menu plan

The only enabled automation plan is `wavefunction-inventory` for the exact official Linux noGUI profile. Its argv is a template containing `<multiwfn-executable>` and `<wavefunction-file>`; stdin contains only `q`. The future executor must substitute verified local paths without persisting them in public artifacts.

Before planning, stream and verify the actual wavefunction basename, bytes, and SHA-256 against the source record. The plan must carry profile/version/platform, source-record SHA-256, verified-wavefunction evidence, executable-digest requirement, literal stdin tokens, ordered prompt/completion sentinels, forbidden sentinels, expected side effects, `dry_run: true`, and `execution_performed: false`.

## Transcript audit

Treat terminal text as untrusted. Read at most 2 MiB, reject NUL and invalid UTF-8, require one banner/update date/load-success/main-menu/graceful-exit sequence, and reject fatal/error markers. Sentinel order matters. A matching transcript raises only `synthetic-validated` maturity until a private authorized executable integration is recorded.

## Charge interchange table

The supported parser consumes this explicit interchange format, not arbitrary console text:

```text
# multiwfn_atomic_charges_v1 method=hirshfeld unit=e
1 H 0.100000
2 H 0.100000
3 O -0.200000
# total_charge=0.000000
```

Require exactly one header, one total, contiguous one-based indices, element order equal to the source manifest, finite charges, and a total equal both to row sum and declared electronic charge within `1e-6 e`. The parser consumes the bytes returned by the one bounded verified read and does not reopen the path. Output is a normalized technical dataset; the method name is metadata, not an endorsement.

## Unsupported routes

Interactive population submenus, topology, basin, grid, bond-order, spectrum, orbital composition, and GUI rendering remain blocked. Add each only with an exact version-specific transcript, deterministic parser, legal real fixture, negative fixture, claim boundary, and tool-integration test.
