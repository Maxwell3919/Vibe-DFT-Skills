# INPUT_CP — NAMELIST: &SYSTEM — Variable: celldm(i), i=1,6

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `aca73fabbaefbf05c94ef57a66aeaaca00946b8746d483975e2b21b436a30ecc`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       celldm(i), i=1,6
      
      Type:           REAL
      See:            ibrav
      Description:    Crystallographic constants - see the "ibrav" variable.
                      Specify either these OR A,B,C,cosAB,cosBC,cosAC NOT both.
                      Only needed values (depending on "ibrav") must be specified
                      alat = celldm(1) is the lattice parameter "a" (in BOHR)
                      If ibrav=0, only celldm(1) is used if present;
                      cell vectors are read from card CELL_PARAMETERS
      +--------------------------------------------------------------------
      
      OR:
      
      +--------------------------------------------------------------------
      Variables:      A, B, C, cosAB, cosAC, cosBC
      
      Type:           REAL
      Description:    Traditional crystallographic constants: a,b,c in ANGSTROM
                        cosAB = cosine of the angle between axis a and b (gamma)
                        cosAC = cosine of the angle between axis a and c (beta)
                        cosBC = cosine of the angle between axis b and c (alpha)
                      The axis are chosen according to the value of "ibrav".
                      Specify either these OR "celldm" but NOT both.
                      Only needed values (depending on "ibrav") must be specified
                      The lattice parameter alat = A (in ANGSTROM )
                      If ibrav = 0, only A is used if present;
                      cell vectors are read from card CELL_PARAMETERS
      +--------------------------------------------------------------------
      
   \\\---
   
```
