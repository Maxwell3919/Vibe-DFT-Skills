# INPUT_PPRISM — NAMELIST: &PLOT — Variable: x0(i), i=1,3

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPRISM.txt
- Retrieved: 2026-07-17T11:49:43+00:00
- Official source SHA-256: `1d61e61afd2d7e18ebc142a14dce2fde77900f0c4f606eb5fc0f0acb89d15d20`
- Extracted text SHA-256: `4946eb4f901d7a44908569661083c8d741ebc8ecd2d8fa592844cbaee6a6ef4e`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       x0(i), i=1,3
      
      Type:           REAL
      Description:    3D vector, origin of the plane (in alat units)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      nx, ny
      
      Type:           INTEGER
      Description:    Number of points in the plane:
                      
                      rho(i,j) = rho( x0 + e1 * (i-1)/(nx-1)
                                 + e2 * (j-1)/(ny-1) ), i=1,nx ; j=1,ny
      +--------------------------------------------------------------------
      
       
   * ELSE IF iflag = 3 : 
   
      THE FOLLOWING VARIABLES ARE OPTIONAL:
      
      +--------------------------------------------------------------------
      Variables:      e1(i), e2(i), e3(i), i=1,3
      
      Type:           REAL
      Description:    3D vectors which determine the plotting parallelepiped
                      (if present, must be orthogonal)
                      
                      "e1", "e2", and "e3" are in alat units !
      +--------------------------------------------------------------------
      
```
