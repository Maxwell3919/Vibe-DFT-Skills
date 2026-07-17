# INPUT_PH — NAMELIST: &INPUTPH — Item: trans

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `3d792707c7881aa8b465a4bd150d13bf53d52b04b9a8a3c71587300c891b6260`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


trans

LOGICAL

Default:

.true.

If .false. the phonons are not computed.
If 
trans
.and. 
epsil
are both .true.,
the effective charges are calculated.
If 
ldisp
is .true., 
trans
=.false. is overridden
(except for the case of electron-phonon calculations)

[
Back to Top
]
```
