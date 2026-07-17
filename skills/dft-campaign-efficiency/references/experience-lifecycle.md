# Experience lifecycle

1. Ingest immutable campaign records.
2. Deduplicate by record id and source-manifest checksum.
3. Classify comparability and evidence completeness.
4. Create a candidate only from repeated accepted evidence.
5. Mark `validated-for-this-campaign` for one protocol/campaign scope.
6. Promote to `cross-campaign-validated` only after independent comparable campaigns support the claimed scope.
7. Attach counterexamples and version/architecture applicability.
8. Mark `superseded` rather than deleting a contradicted rule.
9. Revalidate recommendations after QE/VASP, compiler, library, scheduler, or hardware changes.

If no safe rule emerges, record `No new transferable experience`; this is a valid outcome.
