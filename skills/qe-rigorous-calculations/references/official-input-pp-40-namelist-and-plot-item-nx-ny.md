# INPUT_PP — NAMELIST: &PLOT — Item: nx, ny

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `10f060227166c1ff885c2fd12248ffeeaebd832834c4cb557b57b2ccc2f60d88`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


nx, 
ny

INTEGER

Number of points in the plane:

rho(i,j) = rho( x0 + e1 * (i-1)/(nx-1)
+ e2 * (j-1)/(ny-1) ), i=1,nx ; j=1,ny

[
Back to Top
]

ELSEIF 
iflag = 3
:

the following variables are OPTIONAL:
```
