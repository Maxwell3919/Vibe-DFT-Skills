# INPUT_PH — NAMELIST: &INPUTPH — Item: alpha_mix(niter)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `deb1483c1cdc4faee02d17b36de1af089bac4aa400340e7a4139fffc75214927`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


alpha_mix(niter)

REAL

Default:

alpha_mix(1)=0.7

Mixing factor (for each iteration) for updating
the scf potential:

vnew(in) = alpha_mix*vold(out) + (1-alpha_mix)*vold(in)

[
Back to Top
]
```
