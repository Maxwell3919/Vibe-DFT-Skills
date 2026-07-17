# INPUT_PPRISM — NAMELIST: &PLOT — Variable: output_format

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPRISM.txt
- Retrieved: 2026-07-17T11:49:43+00:00
- Official source SHA-256: `1d61e61afd2d7e18ebc142a14dce2fde77900f0c4f606eb5fc0f0acb89d15d20`
- Extracted text SHA-256: `3d11909f806ce8b4e01456adf481e46a5261ad5cda45b0261e0c26da31ec9858`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       output_format
   
   Type:           INTEGER
   Status:         REQUIRED
   Description:    (ignored on 1D plot)
                   
                   0  = format suitable for gnuplot   (1D)
                   
                   1  = obsolete format no longer supported
                   
                   2  = format suitable for plotrho   (2D)
                   
                   3  = format suitable for XCRYSDEN  (2D or user-supplied 3D region)
                   
                   4  = obsolete format no longer supported
                   
                   5  = format suitable for XCRYSDEN  (3D, using entire FFT grid)
                   
                   6  = format as gaussian cube file  (3D)
                        (can be read by many programs)
                   
                   7  = format suitable for gnuplot   (2D) x, y, f(x,y)
   +--------------------------------------------------------------------
   
```
