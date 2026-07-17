# Validation data and generality policy

Use this policy whenever developing or validating a parser, analysis routine, tool adapter, or plot against real calculation artifacts.

## Preserve the library boundary

- Keep bundled code independent of material names, chemical expectations, project layouts, campaign ids, remote hosts, and selected scientific cases.
- Accept legitimate variability through explicit inputs: species and atom groups, coordinate regions, energy windows, reference energies, spin conventions, k/q labels, bands, modes, tolerances, and aggregation rules.
- Implement generic observable calculations and numerical checks. Do not embed case-specific physical explanations, material screening decisions, or publication conclusions.
- Leave one-off analysis in the project processing directory. Move code into the skill only after extracting a reusable algorithm and testing its configurable boundaries.

## Select real validation data safely

1. Use only local or remote sources that the user authorized.
2. Read the applicable host and nearest project rules before inspecting artifacts.
3. Treat remote sources as read-only. Do not start calculations, alter files, or clean scratch while collecting validation evidence.
4. Select the smallest artifact set that exercises the format and observable. Never copy POTCAR contents.
5. Keep private raw artifacts, unpublished values, host names, accounts, and real paths outside Git. Use a Git-ignored external fixture root for local integration tests.
6. Record runtime provenance outside the skill source: source host, exact path, file role, byte size, SHA-256 when practical, DFT code/version, collection time, and any redaction or partial-copy boundary.

## Separate validation maturity

Label each implementation as one of:

- `design-only`: interface and contract only;
- `synthetic-validated`: internal logic tested with constructed data;
- `format-fixture-validated`: parser tested against a documented format fixture;
- `real-artifact-validated`: tested against a real calculation artifact;
- `tool-integration-validated`: executable invocation and collection tested end to end.

Never use a higher label without its corresponding evidence. A real artifact from one case validates the exercised format path, not every software version or physical regime.

## Show evidence to the user

For every completed real-data validation, return all of the following in the same response:

1. a source table containing the runtime host/path, selected files, roles, sizes or hashes, and why each file was selected;
2. a compact source-data preview, such as headers, metadata, dimensions, or representative records, without dumping large files;
3. the normalized numerical outputs and validation checks;
4. every generated figure embedded from an absolute local path after visual inspection;
5. the maturity label, supported claims, unsupported claims, and parser/tool limitations.

Do not report completion by pointing only to an artifact directory. If no figure is appropriate, state `No figure produced` and explain why.
