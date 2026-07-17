# Quantum ESPRESSO release notes — Fixed in version 1.1.0 (f90) and 1.0.2 (f77):

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `da9143d9bd3bcf6f89032b7d1c6548dd44118e1e46bdc352491f35f4e658bc00`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 1.1.0 (f90) and 1.0.2 (f77): 

  * an inconsistency in the indexing of pseudopotential arrays could
    yield bad dielectric tensors and effective charges if atoms where
    not listed as first all atoms of type 1, then all atoms of type 2,
    and so on (found by Nathalie Vast)
  * phonon with ibrav=0 was not working (info on symm_type was lost:
    found by Michele Lazzeri)
  * the generation of the two random matrices needed in the calculation
    of third order derivatives was incorrect because the random seed
    was not reset. This produced crazy results for q<>0 calculations.
  * the check on existence of tmp_dir did not work properly on 
    Compaq (formerly Dec) alphas (thanks to Guido Roma and Alberto
    Debernardi).
  * a system containing local pseudopotentials only (i.e. H)
    produced a segmentation fault error
  * getenv was incorrectly called on PC's using Absoft compiler:
    the default pseudopotential directory was incorrect
  * out-of-bound bug in pplib/dosg.f fixed. It could have caused
    mysterious crashes or weird results in DOS calculations using
    gaussian broadening.  Thanks to Gun-Do Lee for fixing the bug.
  * a missing initialization to zero in gen_us_dy.F could have
    yielded a wrong stress in some cases
  * phonons in an insulator did not work if more bands (nbnd) 
    were specified than filled valence band only
  * electron-phonon calculation was incorrect if nonlocal PPs
    were used (that is, almost always)
  * Real space term in third order derivative of ewald energy
    was missing (not exactly a bug, but introduced a small error
    that could be not negligible in some cases)
  * bad call in dynmat.f corrected 
  * compilation problems for PC clusters fixed (thanks to Nicola Marzari)

                                 * * * * *
```
