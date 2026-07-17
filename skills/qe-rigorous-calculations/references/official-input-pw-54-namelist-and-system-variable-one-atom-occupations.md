# INPUT_PW — NAMELIST: &SYSTEM — Variable: one_atom_occupations

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `3bed16cb6c8731f852fc075438e5ba46fa99b6e37f59d630de1cde711fd07921`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       one_atom_occupations
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    This flag is used for isolated atoms ("nat"=1) together with
                   "occupations"='from_input'. If it is .TRUE., the wavefunctions
                   are ordered as the atomic starting wavefunctions, independently
                   from their eigenvalue. The occupations indicate which atomic
                   states are filled.
                   
                   The order of the states is written inside the UPF pseudopotential file.
                   In the scalar relativistic case:
                   S -> l=0, m=0
                   P -> l=1, z, x, y
                   D -> l=2, r^2-3z^2, xz, yz, xy, x^2-y^2
                   
                   In the noncollinear magnetic case (with or without spin-orbit),
                   each group of states is doubled. For instance:
                   P -> l=1, z, x, y for spin up, l=1, z, x, y for spin down.
                   Up and down is relative to the direction of the starting
                   magnetization.
                   
                   In the case with spin-orbit and time-reversal
                   ("starting_magnetization"=0.0) the atomic wavefunctions are
                   radial functions multiplied by spin-angle functions.
                   For instance:
                   P -> l=1, j=1/2, m_j=-1/2,1/2. l=1, j=3/2,
                        m_j=-3/2, -1/2, 1/2, 3/2.
                   
                   In the magnetic case with spin-orbit the atomic wavefunctions
                   can be forced to be spin-angle functions by setting
                   "starting_spin_angle" to .TRUE..
   +--------------------------------------------------------------------
   
```
