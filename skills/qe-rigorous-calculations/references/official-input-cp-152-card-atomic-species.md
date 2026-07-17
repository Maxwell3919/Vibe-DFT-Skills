# INPUT_CP — CARD: ATOMIC_SPECIES

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `2c1131ece5cdc0c0a095ebca888a8d5d1a1d7d4c3954b22c65afe6d39f4ce2e2`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_SPECIES 

   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      ATOMIC_SPECIES 
         X(1)     Mass_X(1)     PseudoPot_X(1)     
         X(2)     Mass_X(2)     PseudoPot_X(2)     
         . . . 
         X(ntyp)  Mass_X(ntyp)  PseudoPot_X(ntyp)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       X
      
      Type:           CHARACTER
      Description:    label of the atom. Acceptable syntax:
                      chemical symbol X (1 or 2 characters, case-insensitive)
                      or chemical symbol plus a number or a letter, as in
                      "Xn" (e.g. Fe1) or "X_*" or "X-*" (e.g. C1, C_h;
                      max total length cannot exceed 3 characters)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       Mass_X
      
      Type:           REAL
      Description:    mass of the atomic species [amu: mass of C = 12]
                      not used if calculation='scf', 'nscf', 'bands'
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       PseudoPot_X
      
      Type:           CHARACTER
      Description:    File containing PP for this species.
                      
                      The pseudopotential file is assumed to be in the new UPF format.
                      If it doesn't work, the pseudopotential format is determined by
                      the file name:
                      
                      *.vdb or *.van     Vanderbilt US pseudopotential code
                      *.RRKJ3            Andrea Dal Corso's code (old format)
                      none of the above  old PWscf norm-conserving format
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
