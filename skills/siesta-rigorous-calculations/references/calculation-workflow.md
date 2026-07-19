# Rigorous SIESTA calculation workflow

## 1. Freeze the question and state

Name the observable, unit, normalization/reference, scientific tolerance and physical state. Identify dimensionality/boundary conditions, structure source, charge/spin, constraints and competing states. Create the immutable scientific plan.

## 2. Establish software and model provenance

Record exact SIESTA version/build and version-matched official sources. Select XC/dispersion/U/SOC/transport approximations and state their scientific limitations. Build pseudopotential schema 2.0 evidence for every species before accepting an input.

## 3. Design localized-basis validation

Record basis size, orbital composition, polarization, confinement/energy shift and any explicit `PAO.Basis`. Test basis incompleteness separately from mesh. For binding/adsorption/intermolecular observables, assess basis-superposition error or a justified alternative. Watch for basis discontinuities across geometry/cell changes.

## 4. Design grid, sampling and SCF validation

Vary `Mesh.Cutoff` and geometry/grid placement when eggbox effects can affect energy/forces/barriers. Converge k sampling or finite-size/vacuum controls for the named observable. Make occupations/temperature, solution method, spin and SCF criteria explicit. Explore competing states and mixing stability instead of accepting the first converged solution.

## 5. Freeze ancestry before downstream work

For restarts, bind exact checkpoint hashes and a technically completed parent identity. For bands/DOS/phonons/optics/transport, require a bundle-verified human-accepted parent task with compatible structure/state/protocol/version and the required artifact role. Do not infer ancestry from filenames or a run-manifest field.

## 6. Preflight, execute only with authorization, and preserve output

Run input audit before execution. If authorized to execute, preserve the exact direct FDF, plan, pseudopotential manifest, parent manifest, executable version and standard output. Do not concatenate retry outputs. Each retry is a separate audited artifact set.

## 7. Audit completion and extract terminal observables

Require unique run boundaries, input-dump equality, version equality, failure/warning absence and SCF convergence. Use extracted final energy/Fermi/forces/wall time only from the hash-bound output. Fixed-cell relaxation additionally requires an unambiguous relaxed marker and final force threshold; all other task validity remains manual unless its profile says otherwise.

## 8. Build evidence-linked convergence series

Change one declared dimension at a time while holding plan/protocol/state/model/lineage fixed. Require distinct input/output/audit hashes and at least three stable-tail points plus preceding points. Investigate nonmonotonicity. Validate every observable that supports the final claim, not only total energy.

## 9. Perform task and physical validation

Apply the task checklist, conservation/symmetry/sum-rule/reference comparisons and known-limit tests appropriate to the claim. Numerical stability under one parameter does not validate the physical model.

## 10. Terminate and learn

Emit the shared immutable pre-decision run manifest at technical completion, stop, or failure; abandonment is represented as an intentional stop with a stated limitation. Never emit or rewrite that manifest at scientific acceptance. Route the later human verdict through the separate decision and post-decision claim chain, artifacts/figures to postprocessing, and privacy-safe performance/decision lessons to campaign efficiency. Never store project experience or restricted runtime data in this skill.
