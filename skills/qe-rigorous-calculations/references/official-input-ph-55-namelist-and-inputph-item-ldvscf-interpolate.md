# INPUT_PH — NAMELIST: &INPUTPH — Item: ldvscf_interpolate

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `4fcbda3d1f43f14384be5c32437b9327eddb04f6ad3b36078bb7578dfb1665d8`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


ldvscf_interpolate

LOGICAL

Default:

.false.

If .true., use Fourier interpolation of phonon potential
to compute the induced part of phonon potential at each
q point. Results of a dvscf_q2r.x run is needed.
Requires 
trans
= .false..

[
Back to Top
]

Optional variables for dvscf interpolation:
```
