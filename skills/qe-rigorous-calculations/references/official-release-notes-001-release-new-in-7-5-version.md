# Quantum ESPRESSO release notes — New in 7.5 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `17e29b61ca0bb79f8efc42714b9763c2769858864bbdc7c8394d9c1c15cda947`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 7.5 version:
  * New Orbital Resolved DFT+U method -E. Macke, I. Timrov 
    (see Macke et al. JCTC  2024 20 (11), 4824-4843) 
  * Interface between Wannier90 and DFT+U to use Wannier functions as
    Hubbard projectors (I. Timrov, A. Carta, C. Ederer et al., arXiv:2411.03937)
  * Extension of pp.x to visualize Hubbard projectors of DFT+U (I. Timrov)
  * Modularization of DFPT routines into dfpt_kernel (Jae-Mo Lihm)
  * End support for PPCG diagonalization (I.C.)
  * CUDA Fortran replaced by OpenACC almost everywhere (I.C., PG)
  * Dynamical quadrupoles, octupoles, and Taylor expansion of the dielectric
    response function, courtesy Francesco Macheda et al.
    (Phys. Rev. B 110, 094306,https://doi.org/10.1103/PhysRevB.110.094306).
  * Implemented NVT dynamics with Nose-Hoover thermostats with Verlet and velocity-Verlet engines
  * Implemented NPT dynamics with Nose-Hoover thermostats, Parrinello-Rahman and Wentzcovich barostats and Beeman MD engine.  
```
