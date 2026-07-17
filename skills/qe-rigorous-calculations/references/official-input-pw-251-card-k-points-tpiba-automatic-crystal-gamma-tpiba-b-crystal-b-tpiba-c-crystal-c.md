# INPUT_PW — CARD: K_POINTS { tpiba | automatic | crystal | gamma | tpiba_b | crystal_b | tpiba_c | crystal_c }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `10e678610c4bf9bc1c1df5232dc4aff29519503fbc58a31506b9737fe0330ecd`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: K_POINTS { tpiba | automatic | crystal | gamma | tpiba_b | crystal_b | tpiba_c | crystal_c }

   ________________________________________________________________________
   * IF tpiba  OR  crystal  OR  tpiba_b  OR  crystal_b OR tpiba_c OR crystal_c : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         K_POINTS tpiba | crystal | tpiba_b | crystal_b | tpiba_c | crystal_c 
            nks
            xk_x(1)    xk_y(1)    xk_z(1)    wk(1)    
            xk_x(2)    xk_y(2)    xk_z(2)    wk(2)    
            . . . 
            xk_x(nks)  xk_y(nks)  xk_z(nks)  wk(nks)  
      
      /////////////////////////////////////////
      
       
   * ELSE IF automatic : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         K_POINTS automatic
            nk1 nk2 nk3 sk1 sk2 sk3
      
      /////////////////////////////////////////
      
       
   * ELSE IF gamma : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         K_POINTS gamma
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { tpiba | automatic | crystal | gamma | tpiba_b | crystal_b | tpiba_c | crystal_c }
      
      Default:        tbipa
      Description:   
                      K_POINTS options are:
       
                      tpiba :
                           read k-points in cartesian coordinates,
                           in units of 2 pi/a (default)
       
                      automatic :
                           automatically generated uniform grid of k-points, i.e,
                           generates ( nk1, nk2, nk3 ) grid with ( sk1, sk2, sk3 ) offset.
                           nk1, nk2, nk3 as in Monkhorst-Pack grids
                           k1, k2, k3 must be 0 ( no offset ) or 1 ( grid displaced
                           by half a grid step in the corresponding direction )
                           BEWARE: only grids having the full symmetry of the crystal
                                   work with tetrahedra. Some grids with offset may not work.
       
                      crystal :
                           read k-points in crystal coordinates, i.e. in relative
                           coordinates of the reciprocal lattice vectors
       
                      gamma :
                           use k = 0 (no need to list k-point specifications after card)
                           In this case wavefunctions can be chosen as real,
                           and specialized subroutines optimized for calculations
                           at the gamma point are used (memory and cpu requirements
                           are reduced by approximately one half).
       
                      tpiba_b :
                           Used for band-structure plots.
                           See Doc/brillouin_zones.pdf for usage of BZ labels;
                           otherwise, k-points are in units of  2 pi/a.
                           nks points specify nks-1 lines in reciprocal space.
                           Every couple of points identifies the initial and
                           final point of a line. pw.x generates N intermediate
                           points of the line where N is the weight of the first point.
       
                      crystal_b :
                           As tpiba_b, but k-points are in crystal coordinates.
                           See Doc/brillouin_zones.pdf for usage of BZ labels.
       
                      tpiba_c :
                           Used for band-structure contour plots.
                           k-points are in units of  2 pi/a. nks must be 3.
                           3 k-points k_0, k_1, and k_2 specify a rectangle
                           in reciprocal space of vertices k_0, k_1, k_2,
                           k_1 + k_2 - k_0: k_0 + \alpha (k_1-k_0)+
                           \beta (k_2-k_0) with 0 <\alpha,\beta < 1.
                           The code produces a uniform mesh n1 x n2
                           k points in this rectangle. n1 and n2 are
                           the weights of k_1 and k_2. The weight of k_0
                           is not used.
       
                      crystal_c :
                           As tpiba_c, but k-points are in crystal coordinates.
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
                      
                      In a non-scf calculation, weights do not affect the results.
                      If you just need eigenvalues and eigenvectors (for instance,
                      for a band-structure plot), weights can be set to any value
                      (for instance all equal to 1).
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      nk1, nk2, nk3
      
      Type:           INTEGER
      Description:    These parameters specify the k-point grid
                      (nk1 x nk2 x nk3) as in Monkhorst-Pack grids.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      sk1, sk2, sk3
      
      Type:           INTEGER
      Description:    The grid offsets;  sk1, sk2, sk3 must be
                      0 ( no offset ) or 1 ( grid displaced by
                      half a grid step in the corresponding direction ).
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
