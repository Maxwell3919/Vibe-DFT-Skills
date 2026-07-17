# INPUT_BAND_INTERPOLATION — CARD: K_POINTS { tpiba_b }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `e9dd16ba45d1efdf18122e3d63b9a2b6dd3a2d659667f10322c34fe6eedca318`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: K_POINTS { tpiba_b }

   ________________________________________________________________________
   * IF tpiba_b : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         K_POINTS  tpiba_b 
            nks
            xk_x(1)    xk_y(1)    xk_z(1)    wk(1)    
            xk_x(2)    xk_y(2)    xk_z(2)    wk(2)    
            . . . 
            xk_x(nks)  xk_y(nks)  xk_z(nks)  wk(nks)  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { tpiba_b }
      
      Default:        none
      Description:   
                      All K_POINTS options other than tpiba_b have been disabled in the interpolation.
       
                      tpiba_b :
                           Used for band-structure plots.
                           See Doc/brillouin_zones.pdf for usage of BZ labels;
                           otherwise, k-points are in units of  2 pi/a.
                           nks points specify nks-1 lines in reciprocal space.
                           Every couple of points identifies the initial and
                           final point of a line. pw.x generates N intermediate
                           points of the line where N is the weight of the first point.
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variable:       nks
      
      Type:           INTEGER
      Description:    Number of supplied special k-points.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      xk_x, xk_y, xk_z, wk
      
      Type:           REAL
      Description:    Special k-points (xk_x/y/z) in the irreducible Brillouin Zone
                      (IBZ) of the lattice (with all symmetries) and weights (wk)
                      See the literature for lists of special points and
                      the corresponding weights.
                      
                      If the symmetry is lower than the full symmetry
                      of the lattice, additional points with appropriate
                      weights are generated. Notice that such procedure
                      assumes that ONLY k-points in the IBZ are provided in input
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


This file has been created by helpdoc utility on Wed Sep 03 14:28:58 CEST 2025
```
