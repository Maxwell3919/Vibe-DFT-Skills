# INPUT_CP — CARD: CELL_PARAMETERS { bohr | angstrom | alat }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `762ce27ff31538fd72618f7eac40a714706017c5b4ad6e785b6fe405424356ca`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: CELL_PARAMETERS { bohr | angstrom | alat }

   OPTIONAL CARD, NEEDED ONLY IF IBRAV = 0 IS SPECIFIED, IGNORED OTHERWISE !
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      CELL_PARAMETERS { bohr | angstrom | alat }
         v1(1)  v1(2)  v1(3)  
         v2(1)  v2(2)  v2(3)  
         v3(1)  v3(2)  v3(3)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { bohr | angstrom | alat }
      
      Description:    'bohr'/'angstrom': lattice vectors in bohr radii / angstrom.
                      'alat' / nothing specified: lattice vectors in units or the
                      lattice parameter (either celldm(1) or a). Not specifing
                      units is DEPRECATED and will not be allowed in the future.
                      If nothing specified and no lattice parameter specified,
                      'bohr' is assumed - DEPRECATED, will no longer be allowed
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variables:      v1, v2, v3
      
      Type:           REAL
      Description:    Crystal lattice vectors:
                          v1(1)  v1(2)  v1(3)    ... 1st lattice vector
                          v2(1)  v2(2)  v2(3)    ... 2nd lattice vector
                          v3(1)  v3(2)  v3(3)    ... 3rd lattice vector
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
