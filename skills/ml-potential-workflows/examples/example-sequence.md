# Deterministic example sequence

The synthetic dataset contains metadata only. It is not scientific training data.

1. Run `audit-dataset` on `synthetic-dataset.json`.
2. Hash the exact resulting `dataset-audit.json` and place that digest in a new
   provider request. Do not reuse the dataset-manifest hash.
3. Freeze explicit provider version, mode, seeds, precision, cutoff, loss, stopping,
   thresholds, slices, environment hash and provider-config hash with
   `plan-training`.
4. An external authorized provider adapter may later create a training/pretrained
   origin record. This candidate cannot do so.
5. Bind a model manifest to the exact dataset-audit and training-plan report hashes,
   then use `audit-model` without opening the artifact.
6. Bind evaluation to all three upstream reports and compare every exact metric to
   the thresholds frozen in the plan.
7. Only after independent test and OOD gates pass, construct a bounded deployment
   envelope with a distinct rollback model and external authorization hash.

At every step, the candidate output remains `no_positive_claim`.
