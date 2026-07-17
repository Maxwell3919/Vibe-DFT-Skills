# INPUT_CP — NAMELIST: &CONTROL — Variable: forc_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `b289f1adeec8eff026f38c76984ca4a29d85eaf3b393905f04c527a439d0144b`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       forc_conv_thr
   
   Type:           REAL
   Default:        1.0D-3
   Description:    convergence threshold on forces (a.u) for ionic
                   minimization: the convergence criterion is satisfied
                   when all components of all forces are smaller than
                   forc_conv_thr.
                   See also etot_conv_thr - both criteria must be satisfied
   +--------------------------------------------------------------------
   
```
