# Artifact contracts

Use the repository `contracts/artifact-manifest.schema.json` as the authoritative interchange format.

Every artifact must identify source run ids, DFT code, artifact type, completion status, structured data files, figure files, validation checks, claim boundaries, tool version, UTC generation time, and executed command.

Paths must be relative to the artifact root. Hash final files after writing. A figure without a structured-data source and validation record is presentation-only and cannot support a numerical claim.
