# INPUT_PH — NAMELIST: &INPUTPH — Item: nogg

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `50907fc3f27be56bdc54360e140f9cb0581c79ea71e871f088a227daf259915d`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


nogg

LOGICAL

Default:

.false.

If .true. disable the "gamma_gamma" trick used to speed
up calculations at q=0 (phonon wavevector) if the sum over
the Brillouin Zone includes k=0 only. The gamma_gamma
trick exploits symmetry and acoustic sum rule to reduce
the number of linear response calculations to the strict
minimum, as it is done in code phcg.x.

[
Back to Top
]
```
