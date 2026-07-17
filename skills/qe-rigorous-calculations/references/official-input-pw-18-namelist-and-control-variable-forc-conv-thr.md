# INPUT_PW — NAMELIST: &CONTROL — Variable: forc_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `f4f6143dc395efbeeb36148d3d2766f8f1cae6004f57bf8c23156522763fcd18`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       forc_conv_thr
   
   Type:           REAL
   Default:        1.0D-3
   Description:    Convergence threshold on forces (a.u) for ionic minimization:
                   the convergence criterion is satisfied when all components of
                   all forces are smaller than "forc_conv_thr".
                   See also "etot_conv_thr" - both criteria must be satisfied
   +--------------------------------------------------------------------
   
```
