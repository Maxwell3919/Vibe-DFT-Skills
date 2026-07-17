# INPUT_Q2R — NAMELIST: &INPUT — Variable: fildyn

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Q2R.txt
- Retrieved: 2026-07-17T11:49:50+00:00
- Official source SHA-256: `d493ae0332d60c865e904223a7db8a6b426570c1a07032946e186c869d5ca4ea`
- Extracted text SHA-256: `d1cc06c5df5ad031f6c19bb6092c0e6d820afdeecab7e169f7fd0721021d9b17`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       fildyn
   
   Type:           CHARACTER
   Status:         REQUIRED
   Description:    Input file name (must be specified).
                   
                   "fildyn"0 contains information on the q-point grid
                   
                   "fildyn"1-N contain force constants C_n = C(q_n),
                        where n = 1,...N, where N is the number of
                        q-points in the irreducible brillouin zone.
                   
                   Normally this should be the same as specified on input
                   to the phonon code.
                   
                   In the non collinear/spin-orbit case the files
                   produced by ph.x are in .xml format. In this case
                   "fildyn" is the same as in the phonon code + the
                   .xml extension.
   +--------------------------------------------------------------------
   
```
