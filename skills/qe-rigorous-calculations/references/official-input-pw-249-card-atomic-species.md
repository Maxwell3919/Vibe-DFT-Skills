# INPUT_PW — CARD: ATOMIC_SPECIES

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `9e47490d481c0cba0ce408228567dab477fa43f1a077eed6ec5aff6eb1735097`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
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
                      Used only when performing Molecular Dynamics run
                      or structural optimization runs using Damped MD.
                      Not actually used in all other cases (but stored
                      in data files, so phonon calculations will use
                      these values unless other values are provided)
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
