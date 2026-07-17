# INPUT_PPRISM — NAMELIST: &PLOT — Variable: radius

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPRISM.txt
- Retrieved: 2026-07-17T11:49:43+00:00
- Official source SHA-256: `1d61e61afd2d7e18ebc142a14dce2fde77900f0c4f606eb5fc0f0acb89d15d20`
- Extracted text SHA-256: `76f6af9d8bcfaf67f2d851721ee28f7032abebfb3d5f136878ce9c92f7e2bf7d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       radius
      
      Type:           REAL
      Description:    Radius of the sphere (alat units), centered at (0,0,0)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      nx, ny
      
      Type:           INTEGER
      Description:    Number of points in the polar plane:
                      
                      phi(i)   = 2 pi * (i - 1)/(nx-1), i=1, nx
                      theta(j) =   pi * (j - 1)/(ny-1), j=1, ny
      +--------------------------------------------------------------------
      
       
   ENDIF
   ________________________________________________________________________
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:28:59 CEST 2025
```
