# Quantum ESPRESSO release notes — Fixed in version 3.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `a87d1110e9f56ef965f86e4da2f84cfa16713b6c0237cbacffdcbb4f36bdd447`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 3.2:

  * In same cases the energy under an external sawtooth potential
    simulating an electric field was not correct
  * Case ibrav=13 fixed for good this time!!!
  * Bug in PH/clinear.f90 for cells having nr1 /= nr2 may have
    affected new electron-phonon algorithm
  * Poor accuracy of routines calculating spherical bessel functions
    for high l and small q - harmless except in very special cases
  * LDA+U with variable-cell dynamics/relaxation was wrong due to
    missing rescaling of the integrals of atomic wavefunctions.
    This bug has been present since at least 3.0 
  * Parallel subspace diagonalization could occasionally fail;
    replaced by a new algorithm that is much more stable 
  * Restart problems in parallel run for two cases:
    1) with pools, 2) with local filesystems

                                 * * * * *
```
