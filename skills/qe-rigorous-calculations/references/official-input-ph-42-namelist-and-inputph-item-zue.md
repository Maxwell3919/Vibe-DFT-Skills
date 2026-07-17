# INPUT_PH — NAMELIST: &INPUTPH — Item: zue

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `1c8667298ea3ca57f032d5b1eaa9aea350d5f23e0109a0a6605cd81219fa1e3b`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


zue

LOGICAL

Default:

.false.

If .true. in a q=0 calculation for a non metal the
effective charges are computed from the phonon
density responses. This is an alternative algorithm,
different from the default one (if 
trans
.and. 
epsil
)
The results should be the same within numerical noise.

[
Back to Top
]
```
