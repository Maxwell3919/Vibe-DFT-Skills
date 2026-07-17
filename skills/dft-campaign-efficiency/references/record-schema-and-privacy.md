# Record schema and privacy

Use `contracts/campaign-record.schema.json`. Store records and SQLite databases outside Git.

Use anonymized `record_id`, `run_manifest_id`, `system_class`, `scientific_protocol_id`, and `configuration_id`. Do not include material formula, project name, private path, host, account, queue name, credential, raw output, or unpublished numerical result unrelated to efficiency validation.

The ingestion tool recursively rejects keys matching private/project identity fields. Hash source manifests locally when traceability is needed; keep the source artifact in its authorized project location.
