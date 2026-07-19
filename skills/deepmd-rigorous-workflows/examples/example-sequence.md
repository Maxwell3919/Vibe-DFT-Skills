# Synthetic offline sequence

This example exercises only the candidate's local metadata gates. It does not read
NumPy payloads, invoke DeePMD-kit, train a model, or authorize execution.

1. Copy `synthetic-layout.json` outside the repository and audit that exact copy:

   ```bash
   python3 -B skills/deepmd-rigorous-workflows/scripts/deepmd_guard.py \
     audit-layout --manifest /tmp/deepmd-example/layout.json \
     --out /tmp/deepmd-example/layout-audit.json
   ```

2. Build a portable training projection using the exact SHA-256 of
   `layout-audit.json`. Declare every provider-sensitive field explicitly; do not
   place private paths or executable commands in the projection.

3. Audit the projection against the same immutable layout report. A passing local
   report still has `claim_ceiling=no_positive_claim` and needs a separately trusted
   environment, provider-schema adapter, and human authorization before execution.

4. After an externally authorized run, create a technical run record bound to the
   exact layout/config/environment/authorization/execution/log/rendered-config
   bytes. Audit it without opening the checkpoint or learning curve.

5. Create a frozen-model manifest bound to the exact run report and source
   checkpoint. The resulting local pass establishes metadata lineage only. Route
   independent test/OOD evaluation and deployment gates to the generic
   `ml-potential-workflows` candidate after both Skills are promoted.

Any mutation of an upstream report changes its SHA-256 and requires rebuilding the
downstream record. Never repair lineage by editing a declared hash in isolation.
