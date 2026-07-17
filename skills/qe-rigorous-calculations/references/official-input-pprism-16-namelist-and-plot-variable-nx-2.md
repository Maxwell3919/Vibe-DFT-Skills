# INPUT_PPRISM — NAMELIST: &PLOT — Variable: nx

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPRISM.txt
- Retrieved: 2026-07-17T11:49:43+00:00
- Official source SHA-256: `1d61e61afd2d7e18ebc142a14dce2fde77900f0c4f606eb5fc0f0acb89d15d20`
- Extracted text SHA-256: `ac0e81cd9bedb7cb482c2f95b8d367170e6ffaa6a7cd85b239b9924c7ef9d7b1`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       nx
      
      Type:           INTEGER
      Description:    number of points in the line:
                      
                      rho(i) = rho( x0 + e1 * (i-1)/(nx-1) ), i=1, nx
      +--------------------------------------------------------------------
      
       
   * ELSE IF iflag = 2 : 
   
      THE FOLLOWING VARIABLES ARE REQUIRED:
      
      +--------------------------------------------------------------------
      Variables:      e1(i), e2(i), i=1,3
      
      Type:           REAL
      Description:    3D vectors which determine the plotting plane (in alat units)
                      
                      BEWARE: e1 and e2 must be orthogonal
      +--------------------------------------------------------------------
      
```
