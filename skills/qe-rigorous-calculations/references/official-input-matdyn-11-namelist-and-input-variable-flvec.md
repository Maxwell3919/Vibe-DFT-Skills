# INPUT_MATDYN — NAMELIST: &INPUT — Variable: flvec

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `bef1b5d3736f06d1de19d51d99a12b8ffa4c95289ec6852c62c02d827943db4d`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       flvec
   
   Type:           CHARACTER
   Description:    output file for normalized phonon displacements
                   (default: 'matdyn.modes'). The normalized phonon displacements
                   are the eigenvectors divided by the square root of the mass,
                   then normalized. As such they are not orthogonal.
   +--------------------------------------------------------------------
   
```
