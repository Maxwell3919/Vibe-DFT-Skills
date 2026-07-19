# Record schema and privacy

Use `contracts/campaign-record.schema.json` only when it represents the case faithfully. Store records, source narratives, and SQLite databases outside Git.

Use anonymized `record_id`, `run_manifest_id`, `system_class`, `scientific_protocol_id`, and `configuration_id`. Do not include material formula, project name, private path, host, account, queue name, credential, raw output, or unpublished numerical result unrelated to efficiency validation.

The ingestion tool recursively rejects keys matching private/project identity fields. Hash source manifests locally when traceability is needed; keep the source artifact in its authorized project location.

The security-corrected v1 schema hash-links every record to its exact raw run-manifest bytes. Completed-unreviewed, failed, and stopped records keep all acceptance references null. Accepted/rejected shapes require a calculation record, human scientific decision, and post-decision claim map, but structural hashes are not human authenticity: the current store refuses those states because no platform trust resolver is available.

The schema remains optimized for one normalized run/configuration comparison. It does not fully represent multistage DAG lineage, partial state gates, curve-valued convergence, independent cross-campaign identity, or speculative work. Preserve those facts in the private case narrative until a versioned schema migration exists; do not overload unrelated fields.
