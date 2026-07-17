# INPUT_PW — CARD: ADDITIONAL_K_POINTS { tpiba | crystal | tpiba_b | crystal_b | tpiba_c | crystal_c }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `4cda6445415516da60e50412ea788fd96be392f37d1db9bdb9400f001f744e12`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ADDITIONAL_K_POINTS { tpiba | crystal | tpiba_b | crystal_b | tpiba_c | crystal_c }

   Optional card. Adds a list of k-points with zero weight, after those used for
   the scf calculation. When doing an EXX calculation and "nq1x", "nq2x" or "nq3x" are
   different from one, also include the required k+q points. The main use of this
   card is to do band plots with EXX.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      ADDITIONAL_K_POINTS tpiba | crystal | tpiba_b | crystal_b | tpiba_c | crystal_c 
         nks_add
         k_x(1)        k_y(1)        k_z(1)        wk_(1)        
         k_x(2)        k_y(2)        k_z(2)        wk_(2)        
         . . . 
         k_x(nks_add)  k_y(nks_add)  k_z(nks_add)  wk_(nks_add)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { tpiba | crystal | tpiba_b | crystal_b | tpiba_c | crystal_c }
      
      Default:        tbipa
      Description:    for the explanation of the K_POINTS' options, see "K_POINTS"
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variable:       nks_add
      
      Type:           INTEGER
      Description:    Number of supplied "additional" k-points.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      k_x, k_y, k_z, wk_
      
      Type:           REAL
      Description:    for the respective explanation, see the "xk_x", "xk_y", "xk_z", "wk"
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
