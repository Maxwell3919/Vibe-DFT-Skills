# INPUT_PW — NAMELIST: &ELECTRONS — Variable: diago_thr_init

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `dd4e8f9c37efc4c2cfca19ef0efe93dbf93572fd5a7bb11d639bc15b9d86e5ba`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       diago_thr_init
   
   Type:           REAL
   Description:    Convergence threshold (ethr) for iterative diagonalization
                   (the check is on eigenvalue convergence).
                   
                   For scf calculations: default is 1.D-2 if starting from a
                   superposition of atomic orbitals; 1.D-5 if starting from a
                   charge density. During self consistency the threshold
                   is automatically reduced (but never below 1.D-13) when
                   approaching convergence.
                   
                   For non-scf calculations: default is ("conv_thr"/N elec)/10.
   +--------------------------------------------------------------------
   
```
