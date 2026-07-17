# INPUT_PP — NAMELIST: &PLOT — Item: output_format

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `d870720d681f382c35c6f43b6dd02c304e44bf4e0e7d9e3067a425e6cde3e29e`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


output_format

INTEGER

(ignored on 1D plot)

0 = format suitable for gnuplot (1D)

1 = obsolete format no longer supported

2 = format suitable for plotrho (2D)

3 = format suitable for XCRYSDEN (2D or user-supplied 3D region)

4 = obsolete format no longer supported

5 = format suitable for XCRYSDEN (3D, using entire FFT grid)

6 = format as gaussian cube file (3D)
(can be read by many programs)

7 = format suitable for gnuplot (2D) x, y, f(x,y)

[
Back to Top
]
```
