# INPUT_MATDYN — CARD: /////////////////////////////////////////

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `158273a9972bd4a299ba5b60860a9d45681c47def132c1690cbd764d9f3e073e`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   CARD:  
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nq
            q_x(1)   q_y(1)   q_z(1)   
            q_x(2)   q_y(2)   q_z(2)   
            . . . 
            q_x(nq)  q_y(nq)  q_z(nq)  
      
      /////////////////////////////////////////
      
      DESCRIPTION OF ITEMS:
      
         +--------------------------------------------------------------------
         Variable:       nq
         
         Type:           INTEGER
         Description:    number of q points
         +--------------------------------------------------------------------
         
         Description:    The format of the q-points specification is:
                         
                         ((q(i,n),i=1,3), n=1,nq)
         +--------------------------------------------------------------------
         Variables:      q_x, q_y, q_z
         
         Type:           REAL
         Description:    q-points in cartesian coordinates, 2pi/a units (a = lattice parameters)
         +--------------------------------------------------------------------
         
   ===END OF CARD==========================================================
   
   
    
ENDIF
________________________________________________________________________


:::: Notes

   If q = 0, the direction qhat (q=>0) for the non-analytic part
   is extracted from the sequence of q-points as follows:
   
   qhat = q(n) - q(n-1)   or   qhat = q(n) - q(n+1)
   
   depending on which one is available and nonzero.
   
   For low-symmetry crystals, specify twice q = 0 in the list
   if you want to have q = 0 results for two different directions
   

This file has been created by helpdoc utility on Wed Sep 03 14:23:32 CEST 2025
```
