# INPUT_CP — CARD: ATOMIC_VELOCITIES

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `efaf3209b8232b6a74b71bddf29c856000cbf113f7b52a922542e5cc37d9a719`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_VELOCITIES 

   OPTIONAL CARD, READS VELOCITIES FROM STANDARD INPUT
   
   when starting with "ion_velocities" = "from_input" it is convenient
   to perform a few steps (~5-10) with a small time step (0.5 a.u.).
   The velocities must be expressed using the same length units
   indicated in the card "ATOMIC_POSITIONS", divided by time
   in atomic units.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      ATOMIC_VELOCITIES 
         V(1)    vx(1)    vy(1)    vz(1)    
         V(2)    vx(2)    vy(2)    vz(2)    
         . . . 
         V(nat)  vx(nat)  vy(nat)  vz(nat)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       V
      
      Type:           CHARACTER
      Description:    label of the atom as specified in "ATOMIC_SPECIES"
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      vx, vy, vz
      
      Type:           REAL
      Description:    atomic velocities along x, y and z direction
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
