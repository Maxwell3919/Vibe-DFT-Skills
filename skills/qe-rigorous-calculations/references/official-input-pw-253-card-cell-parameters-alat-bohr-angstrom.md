# INPUT_PW — CARD: CELL_PARAMETERS { alat | bohr | angstrom }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `9d1fc66ae4859d3aecb2380c50b3bb5b42ac3fae03e22c6e0c7e5134be70f0ec`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: CELL_PARAMETERS { alat | bohr | angstrom }

   OPTIONAL CARD, MUST BE PRESENT IF "IBRAV" == 0, MUST BE ABSENT OTHERWISE
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      CELL_PARAMETERS { alat | bohr | angstrom }
         v1(1)  v1(2)  v1(3)  
         v2(1)  v2(2)  v2(3)  
         v3(1)  v3(2)  v3(3)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { alat | bohr | angstrom }
      
      Description:    Unit for lattice vectors; options are:
                      
                      'bohr' / 'angstrom':
                                           lattice vectors in bohr-radii / angstrom.
                                           In this case the lattice parameter alat = sqrt(v1*v1).
                      
                      'alat' / nothing specified:
                                           lattice vectors in units of the lattice parameter (either
                                           "celldm"(1) or "A"). Not specifying units is DEPRECATED
                                           and will not be allowed in the future.
                      
                      If neither unit nor lattice parameter are specified,
                      'bohr' is assumed - DEPRECATED, will no longer be allowed
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variables:      v1, v2, v3
      
      Type:           REAL
      Description:    Crystal lattice vectors (in cartesian axis):
                          v1(1)  v1(2)  v1(3)    ... 1st lattice vector
                          v2(1)  v2(2)  v2(3)    ... 2nd lattice vector
                          v3(1)  v3(2)  v3(3)    ... 3rd lattice vector
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
