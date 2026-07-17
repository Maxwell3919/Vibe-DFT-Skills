# Quantum ESPRESSO release notes — Fixed in 5.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `513a9a0408eabfe833295c5824c1b9aefd576d310dad16ec24cbc85ab3ce729d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.1 version:

  * PWscf: bug in finite electric field in non-collinear case
  * PHonon: G=0 component of the deformation potential at q=0 was incorrect
    (the contribution from the average coulomb potential, i.e. the integral 
    of the Coulomb contribution on the unit cell, was missing). For more 
    details, see M. Calandra et al. Phys. Rev. B 82 165111 , section III B.
  * PWscf: spin-polarized HSE for PAW was incorrectly implemented
  * PHonon: Gamma-specific code wasn't properly restarting in parallel
  * PHonon: epsil + paw was not working with k-point parallelization.
  * PHonon: problem with the symmetry analysis in D_6h. The problem appeared
    in special cases after the symmetry reshuffling made by the phonon code.
  * PWscf: starting with uniform charge worked only for non-spin-polarized
    calculations. Not a big deal unless one used HGH or other pseudopotentials
    without atomic charge information
  * PWscf: Forces with finite electric field (lelfield=.true.) and US PP
    were incorrect in parallel execution
  * D3: bug when the crystal has symmetry but the small group of the 
    q-point has no symmetry.
  * Bogus "file not found" error in pp.x when extracting quantities not
    requiring wave functions if these were "collected" - v.5.0.2 only
  * Some quantities calculated in real space (including the charge itself
    when tqr=.true.) were not always accurately computed in parallel
    execution if the number of planes wasn't the same for all processors
  * Bogus symmetry error in NEB due to missing re-initialization
    of fractional translations

                               * * * * *
```
