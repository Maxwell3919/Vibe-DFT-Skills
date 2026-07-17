# INPUT_PH — NAMELIST: &INPUTPH — Item: nk1, nk2, nk3, k1, k2, k3

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `78cc0ce37dfcfd2cb4b523ea1661238ec95801c13a32540d2fcba616ec62963f`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


nk1, 
nk2, 
nk3, 
k1, 
k2, 
k3

INTEGER

Default:

0,0,0,0,0,0

When these parameters are specified the phonon program
runs a pw non-self consistent calculation with a different
k-point grid thant that used for the charge density.
This occurs even in the Gamma case.

nk1
, 
nk2
, 
nk3
are the parameters of the Monkhorst-Pack grid
with offset determined by 
k1
, 
k2
, 
k3
.

[
Back to Top
]
```
