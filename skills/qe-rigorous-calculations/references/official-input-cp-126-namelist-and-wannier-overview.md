# INPUT_CP — NAMELIST: &WANNIER — overview

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `8c5b2d584d5f30a5e9099ba5a1b44a2b8bde7fe9b807d80bb406dca64c02f46d`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
NAMELIST: &WANNIER

   ONLY IF CALCULATION = 'CP-WF', 'VC-CP-WF'
   
   Output files used by Wannier Function options are the following
   
         fort.21: Used only when calwf=5, contains the full list of g-vecs.
         fort.22: Used Only when calwf=5, contains the coeffs. corresponding
                  to the g-vectors in fort.21
         fort.24: Used with calwf=3,contains the average spread
         fort.25: Used with calwf=3, contains the individual Wannier
                  Function Spread of each state
         fort.26: Used with calwf=3, contains the wannier centers along a
                  trajectory.
         fort.27: Used with calwf=3 and 4,  contains some general runtime
                  information from ddyn, the subroutine that actually
                  does the localization of the orbitals.
         fort.28: Used only if efield=.TRUE. , contains the polarization
                  contribution to the total energy.
   
   Also, The center of mass is fixed during the Molecular Dynamics.
   
   BEWARE : THIS WILL ONLY WORK IF THE NUMBER OF PROCESSORS IS LESS THAN OR
            EQUAL TO THE NUMBER OF STATES.
   
   Nota Bene 1:   For calwf = 5, wffort is not used. The
                  Wannier/Wave(function) coefficients are written to unit 22
                  and the corresponding g-vectors (basis vectors) are
                  written to unit 21. This option gives the g-vecs and
                  their coeffs. in reciprocal space, and the coeffs. are
                  complex. You will have to convert them to real space
                  if you want to plot them for visualization. calwf=1 gives
                  the orbital densities in real space, and this is usually
                  good enough for visualization.
   
```
