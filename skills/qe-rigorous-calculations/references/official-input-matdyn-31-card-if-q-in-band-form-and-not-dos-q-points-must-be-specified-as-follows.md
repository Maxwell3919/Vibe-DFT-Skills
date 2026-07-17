# INPUT_MATDYN — CARD: IF ("Q_IN_BAND_FORM" .AND. .NOT."DOS") Q-POINTS MUST BE SPECIFIED AS FOLLOWS:

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `7e33d049a1db5b1dd32be690c7610f8e6d444024a4c82232db07b31e4182ea02`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   CARD:  
   
      IF ("Q_IN_BAND_FORM" .AND. .NOT."DOS") Q-POINTS MUST BE SPECIFIED AS FOLLOWS:
      
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            nq
            q_x(1)   q_y(1)   q_z(1)   nptq(1)   
            q_x(2)   q_y(2)   q_z(2)   nptq(2)   
            . . . 
            q_x(nq)  q_y(nq)  q_z(nq)  nptq(nq)  
      
      /////////////////////////////////////////
      
      DESCRIPTION OF ITEMS:
      
         +--------------------------------------------------------------------
         Variable:       nq
         
         Type:           INTEGER
         Description:    number of q points
         +--------------------------------------------------------------------
         
         Description:    The format of the q-points specification is:
                         
                         (q(i,n),i=1,3), nptq
                         
                         nptq is the number of points between this point
                         and the next. These points are automatically
                         generated. the q points are given in Cartesian
                         coordinates, 2pi/a units (a = lattice parameters)
         +--------------------------------------------------------------------
         Variables:      q_x, q_y, q_z
         
         Type:           REAL
         Description:    coordinates of the Q point
         +--------------------------------------------------------------------
         
         +--------------------------------------------------------------------
         Variable:       nptq
         
         Type:           INTEGER
         Description:    The number of points between this point and the next.
                         
                         "nptq" is the number of points between this point
                         and the next. These points are automatically
                         generated. the q points are given in Cartesian
                         coordinates, 2pi/a units (a = lattice parameters)
         +--------------------------------------------------------------------
         
   ===END OF CARD==========================================================
   
   
    
* ELSE IF dos == .false. : 

   IF (.NOT. "DOS") Q-POINTS MUST BE SPECIFIED AS FOLLOWS:
   
   ========================================================================
```
