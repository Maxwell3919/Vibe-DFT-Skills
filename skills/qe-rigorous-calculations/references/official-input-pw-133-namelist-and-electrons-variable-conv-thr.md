# INPUT_PW — NAMELIST: &ELECTRONS — Variable: conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `fe79d3a778689e5bc5a9a15de0818fa821e7e8005da12ee55acb219613777bc8`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       conv_thr
   
   Type:           REAL
   Default:        1.D-6
   Description:    Convergence threshold for selfconsistency:
                      estimated energy error < conv_thr
                   (note that conv_thr is extensive, like the total energy).
                   
                   For non-self-consistent calculations, conv_thr is used
                   to set the default value of the threshold (ethr) for
                   iterative diagonalization: see "diago_thr_init"
   +--------------------------------------------------------------------
   
```
