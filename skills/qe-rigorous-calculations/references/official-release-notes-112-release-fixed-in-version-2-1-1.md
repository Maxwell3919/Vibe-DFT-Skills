# Quantum ESPRESSO release notes — Fixed in version 2.1.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b88863173ca687e25dc2a544a7f359738a8e073f8aa92b77f76d0a4d3d7a5a0c`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 2.1.1:

  * memory leak in Raman code
  * disproportionate memory requirement in phonon code with USPP
  * dangerous calls to read_restart_tetra and write_restart_tetra
    when restarting with no allocated tetrahedra
  * vc-relax was not working
  * projwfc failed with lda+U 
  * incorrect automatic generation of k-points in the non colinear case:
    inversion symmetry is not always present because of the presence of  
    a magnetic field in the Hamiltonian
  * electron-phonon calculation was not working if called directly
    after a phonon calculation
  * PWCOND + FFTW + parallel execution = not good
  * cell minimization with steepest descent was not working (CP/FPMD)
  * various Alpha, IBM, SGI, SUN, PGI compilation problems

                                 * * * * *
```
