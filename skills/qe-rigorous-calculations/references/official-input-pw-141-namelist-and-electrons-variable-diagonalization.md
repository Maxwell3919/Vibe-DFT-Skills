# INPUT_PW — NAMELIST: &ELECTRONS — Variable: diagonalization

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `daf9e8d5dfe90097f1119eed22c016f48223aa954d5ca681e325661fb05a3200`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       diagonalization
   
   Type:           CHARACTER
   Default:        'david'
   Description:   
                   Available options are:
    
                   'david' :
                        Davidson iterative diagonalization with overlap matrix
                        (default). Fast, may in some rare cases fail.
    
                   'cg' :
                        Conjugate-gradient-like band-by-band diagonalization.
                        MUCH slower than 'david' but uses less memory and is
                        (a little bit) more robust.
    
                   'ppcg' :
                        PPCG iterative diagonalization (end support on Dec 2024)
    
                   'paro', 'ParO' :
                        ParO iterative diagonalization
    
                   'rmm-davidson', 'rmm-paro' :
                        RMM-DIIS iterative diagonalization.
                        To stabilize the SCF loop
                        RMM-DIIS is alternated with calls to Davidson or
                        ParO  solvers depending on the string used.
                        Other variables that can be used to tune the behavior of
                        RMM-DIIS are:  "diago_rmm_ndim" and "diago_rmm_conv"
   +--------------------------------------------------------------------
   
```
