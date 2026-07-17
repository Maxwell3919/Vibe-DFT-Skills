# INPUT_PPRISM — NAMELIST: &PLOT — Variable: x0(i), i=1,3

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPRISM.txt
- Retrieved: 2026-07-17T11:49:43+00:00
- Official source SHA-256: `1d61e61afd2d7e18ebc142a14dce2fde77900f0c4f606eb5fc0f0acb89d15d20`
- Extracted text SHA-256: `76e048e8e9ea576c3cffdbca89a33650b82abbb87959f91db49b83cb4616652b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       x0(i), i=1,3
      
      Type:           REAL
      Description:    3D vector, origin of the parallelepiped
                      
                      "x0" is in alat units !
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      nx, ny, nz
      
      Type:           INTEGER
      Description:    Number of points in the parallelepiped:
                      
                      rho(i,j,k) = rho( x0 + e1 * (i-1)/nx
                                       + e2 * (j-1)/ny
                                       + e3 * (k-1)/nz ),
                                  i = 1, nx ; j = 1, ny ; k = 1, nz
                      
                      - If "output_format" = 3 (XCRYSDEN), the above variables
                        are used to determine the grid to plot.
                      
                      - If "output_format" = 5 (XCRYSDEN), the above variables
                        are ignored, the entire FFT grid is written in the
                        XCRYSDEN format - works for any crystal axis (VERY FAST)
                      
                      - If "e1", "e2", "e3", "x0" are present,
                        and "e1", "e2", "e3" are parallel to xyz
                        and parallel to crystal axis, a subset of the FFT
                        grid that approximately covers the parallelepiped
                        defined by "e1", "e2", "e3", "x0", is
                        written - untested, might be obsolete
                      
                      - Otherwise, the required 3D grid is generated from the
                        Fourier components (may be VERY slow)
      +--------------------------------------------------------------------
      
       
   * ELSE IF iflag = 4 : 
   
      THE FOLLOWING VARIABLES ARE REQUIRED:
      
```
