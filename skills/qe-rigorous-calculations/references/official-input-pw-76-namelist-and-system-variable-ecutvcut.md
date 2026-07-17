# INPUT_PW — NAMELIST: &SYSTEM — Variable: ecutvcut

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `b94ffa77321ede9b4bdce0d89f35aa3e082fdde8ba19927e4957d5389e866c02`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ecutvcut
   
   Type:           REAL
   Default:        0.0 Ry
   See:            exxdiv_treatment
   Description:    Reciprocal space cutoff for correcting Coulomb potential
                   divergencies at small q vectors.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nqx1, nqx2, nqx3
   
   Type:           INTEGER
   Description:    Three-dimensional mesh for q (k1-k2) sampling of
                   the Fock operator (EXX). Can be smaller than
                   the number of k-points.
                   
                   Currently this defaults to the size of the k-point mesh used.
                   In QE =< 5.0.2 it defaulted to nqx1=nqx2=nqx3=1.
   +--------------------------------------------------------------------
   
```
