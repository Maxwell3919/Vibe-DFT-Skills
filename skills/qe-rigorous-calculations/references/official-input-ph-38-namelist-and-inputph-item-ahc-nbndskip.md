# INPUT_PH — NAMELIST: &INPUTPH — Item: ahc_nbndskip

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `bfc14b48765a425e6e74ecd7524f8e8ae3c70af43124aff537185dcdadc704e5`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


ahc_nbndskip

INTEGER

Default:

0

Number of bands to exclude when computing the self-energy. Self-energy
is computed for bands with indices from 
ahc_nbndskip
+1 to

ahc_nbndskip
+
ahc_nbnd
. 
ahc_nbndskip
+
ahc_nbnd
cannot
exceed nbnd of the preceding SCF or NSCF calculation.

[
Back to Top
]
```
