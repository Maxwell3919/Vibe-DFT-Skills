# INPUT_PH — NAMELIST: &INPUTPH — Item: epsil

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `ed5a4b827a1d4e6acb06da00bb40877e69136c6222e8f1fdc54691288695624d`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


epsil

LOGICAL

Default:

.false.

If .true. in a q=0 calculation for a non metal the
macroscopic dielectric constant of the system is
computed. Do not set 
epsil
to .true. if you have a
metallic system or q/=0: the code will complain and stop.

Note: the input value of 
epsil
will be ignored if 
ldisp
=.true.
(the code will automatically set 
epsil
to .false. for metals,
to .true. for insulators: see routine PHonon/PH/prepare_q.f90).

[
Back to Top
]
```
