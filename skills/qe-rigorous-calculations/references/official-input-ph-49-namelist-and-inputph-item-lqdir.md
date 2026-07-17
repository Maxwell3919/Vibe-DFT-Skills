# INPUT_PH — NAMELIST: &INPUTPH — Item: lqdir

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `adef17c2abbc4b0b5b3a929d0a2a2f6206d24196dae97cea0bf9750769ab3166`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


lqdir

LOGICAL

Default:

.false.

If .true. ph.x creates inside outdir a separate subdirectory
for each q vector. The flag is set to .true. when 
ldisp
=.true.
and 
fildvscf
/= ' ' or when an electron-phonon
calculation is performed. The induced potential is saved
separately for each q inside the subdirectories.

[
Back to Top
]
```
