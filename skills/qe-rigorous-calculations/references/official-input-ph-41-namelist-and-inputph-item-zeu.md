# INPUT_PH — NAMELIST: &INPUTPH — Item: zeu

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `81acb222708d5de3ccecab511b18825c6b93d835b2437fce013567c0de4bcef2`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


zeu

LOGICAL

Default:

zeu=
epsil

If .true. in a q=0 calculation for a non metal the
effective charges are computed from the dielectric
response. This is the default algorithm. If 
epsil
=.true.
and 
zeu
=.false. only the dielectric tensor is calculated.

[
Back to Top
]
```
