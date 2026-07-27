# VASP calculation workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md`. Record the user's explicit
`off`, `silent-update`, or `milestone-review` selection before the first
calculation side effect. Taskbook mode controls pauses, not execution authority
or scientific decisions.

Place `INCAR`, `POSCAR`, `KPOINTS`, runtime-only `POTCAR`, and intentional
restart inputs together under one `02-inputs/<stage-id>/<input-set-id>/`.
Generate `input-set.json`; it records hashes, never POTCAR content outside the
local calculation workspace. In review mode, freeze the input set with the
workflow plan and obtain the exact-hash initial review decision before
`init-attempt`.

Give every launch or retry a new `03-runs/<stage-id>/<attempt-id>/`. Keep native
inputs, stdout/stderr, outputs, restart ancestry, scheduler identity, run
manifest, and audits together. Never move an active VASP workdir. Append
lifecycle events from observed VASP and scheduler evidence.

Use typed `structure`, `input`, `execution`, `data`, and `figure` milestones for
stable artifacts. Run `check` before handoff and `check --require-quiescent`
before moving, cleaning, or archiving an attempt.
