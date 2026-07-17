# INPUT_PP — NAMELIST: &INPUTPP — Item: spin_component

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `6080e8153e95f835bb240dd02543e521ad025a0cd6187b32f9bc6edc6eae357e`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


spin_component

INTEGER

Default:

0

0 = spin averaged potential (default value),
1 = spin up potential,
2 = spin down potential.

[
Back to Top
]

ELSEIF 
plot_num=3
:

Options for LDOS (plot_num=3):
LDOS is plotted on grid [emin, emax] with spacing delta_e.
```
