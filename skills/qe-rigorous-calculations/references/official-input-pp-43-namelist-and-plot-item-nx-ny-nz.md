# INPUT_PP — NAMELIST: &PLOT — Item: nx, ny, nz

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `5f422ac285e3d7c7c996466aa3684405805c302dbba00f21222d90607c1652ab`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


nx, 
ny, 
nz

INTEGER

Number of points in the parallelepiped:

rho(i,j,k) = rho( x0 + e1 * (i-1)/nx
+ e2 * (j-1)/ny
+ e3 * (k-1)/nz ),
i = 1, nx ; j = 1, ny ; k = 1, nz

- If 
output_format
= 3 (XCRYSDEN), the above variables
are used to determine the grid to plot.

- If 
output_format
= 5 (XCRYSDEN), the above variables
are ignored, the entire FFT grid is written in the
XCRYSDEN format - works for any crystal axis (VERY FAST)

- If 
e1
, 
e2
, 
e3
, 
x0
are present,
and 
e1
, 
e2
, 
e3
are parallel to xyz
and parallel to crystal axis, a subset of the FFT
grid that approximately covers the parallelepiped
defined by 
e1
, 
e2
, 
e3
, 
x0
, is
written - untested, might be obsolete

- Otherwise, the required 3D grid is generated from the
Fourier components (may be VERY slow)

[
Back to Top
]

ELSEIF 
iflag = 4
:

the following variables are REQUIRED:
```
