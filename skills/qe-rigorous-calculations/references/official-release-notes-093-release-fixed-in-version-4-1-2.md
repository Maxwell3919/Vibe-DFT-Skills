# Quantum ESPRESSO release notes — Fixed in version 4.1.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `48b92aa77e9b0e381deccfc68ce9f2dabf87a52dd425c73028103b076ac7677e`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.1.2:

  * fixed nonstandard C construct in memstat.c that picky compilers didn't like
  * PBEsol keyword wasn't properly recognized
  * call to invsym with overlapping input and output matrix could 
    result in bogus error message
  * cp.x: update of dt with autopilot wasn't working
  * for some magnetic point groups, having rotation+time reversal
    symmetries, the k-point reduction was not correctly done
  * wavefunctions for extrapolation written to wfcdir and not to outdir
  * Some constraints were not working in solids, due to an incorrect
    estimate of the maximum possible distance between two atoms
  * Parallel execution of D3 wasn't working in at least some cases
    (e.g. with k-point parallelization) since a long time
  * restart of phonon code with PAW wasn't working

                                * * * * *
```
