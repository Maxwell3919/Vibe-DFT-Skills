# CP2K external-tool adapters

Prefer official CP2K-community tools when available, but keep their evidence distinct from bundled scientific gates.

## Capability check

Check without installing or mutating the environment:

```bash
python3 scripts/probe_cp2k_tools.py --pretty
```

The bundled probe only inspects command/package availability. It does not execute a detected program or emit its path. Availability alone has no maturity effect.

## cp2k-input-tools

Official repository: `https://github.com/cp2k/cp2k-input-tools`.

- Use `cp2klint` for syntax/schema validation.
- Use `fromcp2k` for a normalized expanded representation when includes and preprocessing are inventoried.
- Use `cp2kget` for targeted restart/input values.
- Bind the CP2K input-definition XML to the executable version.
- Treat success as parser/schema evidence only; continue method, task, convergence and physical gates.

Never allow an untrusted include to escape the authorized case root. Never install the package without user authorization.

## cp2k-output-tools

Official repository: `https://github.com/cp2k/cp2k-output-tools`.

- Use `cp2kparse` for structured output values.
- Use `xyz_restart_cleaner` to remove duplicated MD frames across restart joins.
- Use `cp2k_bs2csv` for CP2K band-structure files.
- Use `cp2k_pdos` only with explicit broadening/grid/reference conventions.

`cp2kparse` may expose user, host, working directory, input filename and data paths. Do not emit its raw JSON. Normalize through a privacy-safe adapter that whitelists numeric values, enums, counts, tool versions and hashes.

## Postprocessing handoff

Send normalized bands/DOS/trajectory/grid data to `$dft-postprocess` with:

- source artifact hashes and safe roles;
- parser/tool name and version;
- CP2K version and parent run id;
- units, energy/reference convention and spin/channel mapping;
- limitations and observable-specific maturity;
- no private path, host, account, raw warning text or unpublished fixture in Git.

An external tool being installed does not raise a workflow maturity level. Require a tested adapter and real-artifact fixture.
