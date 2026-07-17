# INPUT_CP — NAMELIST: &CONTROL — Variable: etot_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `0cc8f5d8d9edce367fcd1ebc695b0db671acf31e885cc65b502c8985a0322170`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       etot_conv_thr
   
   Type:           REAL
   Default:        1.0D-4
   Description:    convergence threshold on total energy (a.u) for ionic
                   minimization: the convergence criterion is satisfied
                   when the total energy changes less than etot_conv_thr
                   between two consecutive scf steps.
                   See also forc_conv_thr - both criteria must be satisfied
   +--------------------------------------------------------------------
   
```
