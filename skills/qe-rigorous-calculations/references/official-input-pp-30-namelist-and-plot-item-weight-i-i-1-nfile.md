# INPUT_PP — NAMELIST: &PLOT — Item: weight(i), i=1,nfile

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `88032b19b5f5043f76433fe8954f08892bf77f939087e8b0c3d9b6ec516609d8`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


weight(i), i=1,nfile

REAL

Default:

weight(1)=1.0

weighing factors: assuming that rho(i) is the quantity
read from filepp(i), the quantity that will be plotted is:

weight(1)*rho(1) + weight(2)*rho(2) + weight(3)*rho(3) + ...

[
Back to Top
]

BEWARE:
atomic coordinates are read from the first file;
if their number is different for different files,
the first file must have the largest number of atoms
```
