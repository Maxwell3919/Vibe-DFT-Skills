# Artifact contracts

Use the repository `contracts/artifact-manifest.schema.json` as the authoritative derived-artifact interchange format. Use `contracts/normalized-dataset.schema.json` for structured observable data, `contracts/postprocess-plan.schema.json` for evidence/parameter-aware plans, and `contracts/tool-execution.schema.json` for external command records.

Every artifact must identify source run ids, DFT code, artifact type, completion status, structured data files, figure files, validation checks, claim boundaries, tool version, UTC generation time, and executed command.

Paths must be relative to the artifact root. Hash final files after writing. A figure without a structured-data source and validation record is presentation-only and cannot support a numerical claim.

Dataset source records retain labels, byte counts, and hashes but not private absolute paths. Store runtime host/path closure in the project provenance area, outside the committed skill repository, and show it to the user during authorized real-data validation.
