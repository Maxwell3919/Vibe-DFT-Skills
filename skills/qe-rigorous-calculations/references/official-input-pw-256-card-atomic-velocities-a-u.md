# INPUT_PW — CARD: ATOMIC_VELOCITIES { a.u }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `4363c22b21127e67336aaaef7784072abcf3deb0b7c1757155294e63f08467ec`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_VELOCITIES { a.u }

   OPTIONAL CARD, READS VELOCITIES FROM STANDARD INPUT
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      ATOMIC_VELOCITIES { a.u }
         V(1)    vx(1)    vy(1)    vz(1)    
         V(2)    vx(2)    vy(2)    vz(2)    
         . . . 
         V(nat)  vx(nat)  vy(nat)  vz(nat)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { a.u }
      
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variable:       V
      
      Type:           CHARACTER
      Description:    label of the atom as specified in ATOMIC_SPECIES
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      vx, vy, vz
      
      Type:           REAL
      Description:    atomic velocities along x y and z direction
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
