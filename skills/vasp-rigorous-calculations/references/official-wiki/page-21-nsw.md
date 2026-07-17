# NSW

- Official URL: https://www.vasp.at/wiki/NSW
- Page ID: 21
- Revision ID: 33294
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

NSW = [integer]
Default: NSW = 0

Description: NSW sets the maximum number of ionic steps.

IBRION = 0:

NSW gives the number of steps in all molecular dynamics runs. It has to be supplied, otherwise VASP exits immediately after having started. We recommend splitting long MD runs containing ab-initio calculations into multiple calculations with NSW⪅20000. For ML_MODE=run larger values of NSW should be possible, but consider setting ML_OUTBLOCK.

IBRION != 0:

In all minimization algorithms (quasi-Newton, conjugate gradient, and damped molecular dynamics) NSW defines the maximum number of ionic steps.

Within each ionic step at most NELM electronic steps are performed. It is fewer if the convergence criterion set by EDIFF is met before. Forces and stresses are calculated according to the setting of ISIF for each ionic step.

Related tags and articles[edit | edit source]

structure optimization, NBLOCK, KBLOCK, ML_OUTBLOCK

Examples that use this tag
