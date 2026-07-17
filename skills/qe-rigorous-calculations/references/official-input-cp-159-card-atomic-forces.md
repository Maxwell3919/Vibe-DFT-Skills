# INPUT_CP — CARD: ATOMIC_FORCES

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `f9bd2ace0fdb6dbb395729d338acf11648421768a573181932c8739c58230b4a`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_FORCES 

   OPTIONAL CARD USED TO SPECIFY EXTERNAL FORCES ACTING ON ATOMS
   
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
      Description:    label of the atom as specified in ATOMIC_SPECIES
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      fx, fy, fz
      
      Type:           REAL
      Description:    external force on atom X (cartesian components, Ha/a.u. units)
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
