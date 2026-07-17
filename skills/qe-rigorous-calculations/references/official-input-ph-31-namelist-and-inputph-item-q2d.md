# INPUT_PH — NAMELIST: &INPUTPH — Item: q2d

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `447b02c5e376cf284ce4af8c02e3cac1534b6a3894b11dd6f2bf50f20215c974`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


q2d

LOGICAL

Default:

.false.

If .true. three q points and relative weights are
read from input. The three q points define the rectangle
q(:,1) + l (q(:,2)-q(:,1)) + m (q(:,3)-q(:,1)) where
0< l,m < 1. The weights are integer and those of points two
and three are the number of points in the two directions.

[
Back to Top
]
```
