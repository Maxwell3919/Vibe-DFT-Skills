# INPUT_CP — CARD: REF_CELL_PARAMETERS { bohr | angstrom }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `c93145a86d5facd8b4cfef832a84afa2d7652695b5350beaab2f3fe3a6d4d88f`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: REF_CELL_PARAMETERS { bohr | angstrom }

         OPTIONAL CARD, NEEDED ONLY IF ONE WANTS TO DO VARIABLE CELL CALCULATIONS ACCURATELY.
   THE REFERENCE CELL GENERATES ADDITIONAL BUFFER PLANEWAVES.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      REF_CELL_PARAMETERS { bohr | angstrom }
         v1(1)  v1(2)  v1(3)  
         v2(1)  v2(2)  v2(3)  
         v3(1)  v3(2)  v3(3)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { bohr | angstrom }
      
      Description:    bohr / angstrom: reference cell parameters in bohr radii / angstrom.
                      
                      To mimic a constant effective planewave kinetic energy (ecfixed) during a
                      variable-cell calculation, the specified reference cell has to be large enough
                      such that the individual cell vector lengths of the fluctuating cell do not
                      exceed the corresponding reference lattice vector lengths during the entire
                      calculation. The cost of the calculation will increase with the increasing
                      size of the reference cell. The user must test for the proper reference cell
                      parameters.
                      
                      The reference cell parameters should be used in conjunction with q2sigma,
                      qcutz, and ecfixed. See q2sigma for more information about mimicking constant
                      effective planewave kinetic energy (ecfixed) during variable-cell calculations.
                      
                      The reference cell parameters should be chosen as an isotropic scaling of the
                      initial cell of the system. This means that the reference cell should have
                      the same shape as the initial simulatoin cell. The reference cell parameters should
                      NOT be changed throughout a given simulatoin. Typically, 2%-10% scaling of
                      the unit cell vectors are sufficient. However, the cell fluctuations depend on
                      the system and the thermodynamic conditions. So again user must test for the proper
                      choice of reference cell parameters.
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variables:      v1, v2, v3
      
      Type:           REAL
      Description:    REF_CELL_PARAMETERS { bohr | angstrom }
                      v1(1)  v1(2)  v1(3)    ... 1st reference lattice vector
                      v2(1)  v2(2)  v2(3)    ... 2nd reference lattice vector
                      v3(1)  v3(2)  v3(3)    ... 3rd reference lattice vector
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
