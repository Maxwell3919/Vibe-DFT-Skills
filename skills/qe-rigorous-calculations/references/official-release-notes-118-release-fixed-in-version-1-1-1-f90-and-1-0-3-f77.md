# Quantum ESPRESSO release notes — Fixed in version 1.1.1 (f90) and 1.0.3 (f77):

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `17fe454f6cb4afd3d85915aa5886aacedf87eea5b4c6e6b7d729d610e76da5fe`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 1.1.1 (f90) and 1.0.3 (f77):

  * LSDA calculations need either gaussian broadening or tetrahedra
    but no input check was performed 
  * restarting from a run interrupted at the end of self-consistency
    yielded wrong forces
  * projwave.F (projection over atomic functions) was not working
    with atoms having semicore states (found by Seungwu Han)
  * stm.F : option stm_wfc_matching was not working properly 
    if symmetry was present (no symmetrization was performed)
  * dynmat.x : displacement patterns in "molden" format were
    incorrectly divided by the square root of atomic masses
  * d3: misc. problems in parallel execution fixed

                                 * * * * *
```
