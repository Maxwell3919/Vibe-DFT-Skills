# INPUT_PW — CARD: ATOMIC_FORCES

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `0eec49ddcb2f99a67c2da40e7cedee53af543522bd9296bb977ac89e9dae4045`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_FORCES 

   OPTIONAL CARD USED TO SPECIFY EXTERNAL FORCES ACTING ON ATOMS.
   
   BEWARE: if the sum of external forces is not zero, the center of mass of
           the system will move
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      ATOMIC_FORCES 
         X(1)    fx(1)    fy(1)    fz(1)    
         X(2)    fx(2)    fy(2)    fz(2)    
         . . . 
         X(nat)  fx(nat)  fy(nat)  fz(nat)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       X
      
      Type:           CHARACTER
      Description:    label of the atom as specified in "ATOMIC_SPECIES"
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      fx, fy, fz
      
      Type:           REAL
      Description:    external force on atom X (cartesian components, Ry/a.u. units)
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
