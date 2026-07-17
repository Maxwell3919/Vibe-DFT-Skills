# INPUT_MATDYN — CARD: IF ("READTAU") ATOMIC POSITIONS MUST BE SPECIFIED AS FOLLOWS:

- Official source: https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt
- Retrieved: 2026-07-17T11:49:20+00:00
- Official source SHA-256: `e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91`
- Extracted text SHA-256: `32a4253eb3d851060638c761694d19b6df50abdfc0ab19c70d96e1b6412671cc`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   CARD:  
   
      IF ("READTAU") ATOMIC POSITIONS MUST BE SPECIFIED AS FOLLOWS:
      
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
            X(1)    Y(1)    Z(1)    ityp(1)    
            X(2)    Y(2)    Z(2)    ityp(2)    
            . . . 
            X(nat)  Y(nat)  Z(nat)  ityp(nat)  
      
      /////////////////////////////////////////
      
      DESCRIPTION OF ITEMS:
      
         +--------------------------------------------------------------------
         Variables:      X, Y, Z
         
         Type:           REAL
         Description:    X, Y, Z atomic positions
         +--------------------------------------------------------------------
         
         +--------------------------------------------------------------------
         Variable:       ityp
         
         Type:           INTEGER
         Description:    index of the atomic type
         +--------------------------------------------------------------------
         
   ===END OF CARD==========================================================
   
   
    
ENDIF
________________________________________________________________________

________________________________________________________________________
* IF q_in_band_form == .true .and. dos == .false. : 

   ========================================================================
```
