# SIESTA scientific plan contract

`create_siesta_plan.py` creates immutable schema 2.0 intent evidence. The audit requires its exact file hash; convergence rows must all bind that same hash.

Required resolved concepts:

- privacy-safe `case_id`, `scientific_protocol_id`, and `state_id`;
- exact SIESTA version and derived documentation line;
- task, periodicity and workflow stage;
- objective and one named observable with unit, normalization and reference;
- finite nonnegative absolute and/or relative tolerance;
- at least one explicit acceptance criterion;
- declared model features such as SOC when applicable;
- deterministic minimum workflow and known limitations.

The generator supports SCF, relaxation, MD, bands, DOS, phonon, optics, RT-TDDFT, TranSIESTA, TBtrans and generic plans. Support in the plan generator means the intent can be represented; it does not mean the task input/run/validity is automated. Consult `task-evidence-profiles.json`.

The plan is create-once and refuses overwrite. If intent changes, create a new plan with a new protocol/state identity rather than editing the old JSON. Any edit after an audit invalidates the plan hash and blocks convergence use.

The plan itself can only conclude `plan_ready`. It does not prove input validity, executable availability, completed execution, convergence, task validity, or scientific acceptance.
