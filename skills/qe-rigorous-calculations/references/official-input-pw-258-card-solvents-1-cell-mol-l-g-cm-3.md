# INPUT_PW — CARD: SOLVENTS { 1/cell | mol/L | g/cm^3 }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `a74374e07c50abf03a3015e2bf552253f8ce027a7cea514acd5987805bae6340`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: SOLVENTS { 1/cell | mol/L | g/cm^3 }

   OPTIONAL CARD, USED ONLY IF "TRISM" = .TRUE., IGNORED OTHERWISE !
   
   ________________________________________________________________________
   * IF laue_both_hands = .FALSE. : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         SOLVENTS { 1/cell | mol/L | g/cm^3 }
            X(1)      Density(1)      Molecule(1)      
            X(2)      Density(2)      Molecule(2)      
            . . . 
            X(nsolv)  Density(nsolv)  Molecule(nsolv)  
      
      /////////////////////////////////////////
      
       
   * ELSE IF laue_both_hands = .TRUE. : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         SOLVENTS { 1/cell | mol/L | g/cm^3 }
            X(1)      Density_Left(1)      Density_Right(1)      Molecule(1)      
            X(2)      Density_Left(2)      Density_Right(2)      Molecule(2)      
            . . . 
            X(nsolv)  Density_Left(nsolv)  Density_Right(nsolv)  Molecule(nsolv)  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { 1/cell | mol/L | g/cm^3 }
      
      Description:   
                      1/cell :
                           solvent's densities are specified
                           as number of molecules in the unit cell.
       
                      mol/L :
                           solvent's densities are specified as molar concentrations.
       
                      g/cm^3 :
                           solvent's densities are in gram per cm^3.
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variable:       X
      
      Type:           CHARACTER
      Description:    label of the solvent molecule.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       Density
      
      Type:           REAL
      Description:    density of the solvent molecule.
                      if not positive value is set, density is read from MOL-file.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       Molecule
      
      Type:           CHARACTER
      Description:    MOL-file of the solvent molecule.
                      in the MOL-file, molecular structure and some other data are written.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       X
      
      Type:           CHARACTER
      Description:    label of the solvent molecule.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       Density_Left
      
      Type:           REAL
      Description:    density of the solvent molecule in the left-hand side.
                      if not positive value is set, density is read from MOL-file.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       Density_Right
      
      Type:           REAL
      Description:    density of the solvent molecule in the right-hand side.
                      if not positive value is set, density is read from MOL-file.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       Molecule
      
      Type:           CHARACTER
      Description:    MOL-file of the solvent molecule.
                      in the MOL-file, molecular structure and some other data are written.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
