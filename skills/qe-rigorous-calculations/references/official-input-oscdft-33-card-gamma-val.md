# INPUT_OSCDFT — CARD: GAMMA_VAL

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `df7cd01817a6ab7602461bcb4871469b9cad1ce4c587b5a909f8e2526e84c493`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: GAMMA_VAL 

   CONDITIONAL CARD, USED ONLY IF "OPTIMIZATION_METHOD" == 'GRADIENT DESCENT2', IGNORED OTHERWISE !
                  THIS CARD CAN BE USED ONLY WITH OSCDFT_TYPE = 1.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      GAMMA_VAL 
         gamma_val(1)         
         gamma_val(2)         
         . . . 
         gamma_val(n_oscdft)  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       gamma_val
      
      Type:           DOUBLE
      Status:         REQUIRED if "optimization_method" == 'gradient descent2'
      Description:    This sets the learning rate for each multipliers,
                      allowing different learning rate for each multipliers.
                      See "optimization_method" for more details.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================



::::  ADDITIONAL NOTES 

   1. The default values are the recommeded options for "convergence_type"
      and "array_convergence_func"
   
   2. When using diagonalization='davidson', OS-CDFT may fail with
      'S matrix not positive definite' as an error. When that occurs,
      use diagonalization='cg'.
   
   3. Use "iteration_type"=0 for most cases. "iteration_type"=0 is faster,
      due to the ability to gradually tighten the convergence threshold.
      However, "iteration_type"=1 is more robust.
   
   4. "orbital_desc" in the "TARGET_OCCUPATION_NUMBERS" card:
      While one "orbital_desc" can be composed of multiple atoms,
      the occupation number may not be accurate.
      For example, 5(3d)6(2s2p) will be accepted, however the
      atomic wavefunction of atom 5 and atom 6 may not be orthogonal.
      (unless "orthogonalize_swfc" is .true.)
   
   5. To use oscdft_type = 2, see the last two examples below as well as
      PW/examples/example15.
   


::::  ADDITIONAL EXAMPLES FOR TARGET_OCCUPATION_NUMBERS 

   Input File:
   &OSCDFT
     oscdft_type=1,
     n_oscdft=2,
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     T UP   5(3d) 5 0.9075202 0.0
     F DOWN 5(3d)
   Explanations:
   Row 1: Apply a constraint on the 5th spin-up occupation number of the
          3d orbital of atom 5 to a target of 0.9075202
   Row 2: Print the occupation numbers of the spin-down occupation numbers
          of the 3d orbital of atom 5
   
   
   Input File:
   &OSCDFT
     oscdft_type=1,
     n_oscdft=2,
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     F UP   1(3d)
     T DOWN 1(3d) 5 0.9369434 0.0
     F UP   2(3d)
     T DOWN 2(3d) 5 0.261727 0.0
   Explanations:
   Row 1: Print the occupation numbers of the spin-up occupation numbers of the
          3d orbital of atom 1
   Row 2: Apply a constraint on the 5th spin-down occupation number of the
          3d orbital of atom 1 to a target of 0.9369434
   Row 3: Print the occupation numbers of the spin-up occupation numbers of the
          3d orbital of atom 2
   Row 4: Apply a constraint on the 5th spin-down occupation number of the
          3d orbital of atom 2 to a target of 0.261727
   
   
   Input File:
   &OSCDFT
     oscdft_type=1,
     n_oscdft=7,
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     T UP    9(3d) sum 4 2 2 3 4 4.0135939 0.0
     T UP    9(3d) sum 4 3 1 3 4 4.0135939 0.0
     T UP    9(3d) sum 4 4 1 2 4 4.0135939 0.0
     T UP    9(3d) sum 4 5 1 2 3 4.0135939 0.0
     F DOWN  9(3d)
     F UP   16(3d)
     F DOWN 16(3d)
   Explanations:
   Row 1-4: Apply a constraint on the sum of the 2nd, 3rd, 4th, and 5th spin-up
            occupation number of the 3d orbital of atom 9 to a target of 4.0135939
   Row 5  : Print the occupation numbers of the spin-down occupation numbers of the
            3d orbital of atom 9
   Row 6  : Print the occupation numbers of the spin-up occupation numbers of the
            3d orbital of atom 16
   Row 7  : Print the occupation numbers of the spin-down occupation numbers of the
            3d orbital of atom 16
   
   
   Input File:
   &OSCDFT
     oscdft_type=1,
     n_oscdft=7,
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     F UP    9(3d)
     F DOWN  9(3d)
     T UP   16(3d) sum 4 2 4 5 6 4.0135939 0.0
     T UP   16(3d) sum 4 3 3 5 6 4.0135939 0.0
     T UP   16(3d) sum 4 4 3 4 6 4.0135939 0.0
     T UP   16(3d) sum 4 5 3 4 5 4.0135939 0.0
     F DOWN 16(3d)
   Explanations:
   Row 1  : Print the occupation numbers of the spin-up occupation numbers of the
            3d orbital of atom 9
   Row 2  : Print the occupation numbers of the spin-down occupation numbers of the
            3d orbital of atom 9
   Row 3-6: Apply a constraint on the sum of the 2nd, 3rd, 4th, and 5th spin-up
            occupation number of the 3d orbital of atom 16 to a target of 4.0135939
   Row 7  : Print the occupation numbers of the spin-down occupation numbers of the
            3d orbital of atom 16
   
   
   Input File:
   &OSCDFT
     oscdft_type=1,
     n_oscdft=7,
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     T UP   39(3d) sum 4 2 2 3 4 4.0135939 0.0
     T UP   39(3d) sum 4 3 1 3 4 4.0135939 0.0
     T UP   39(3d) sum 4 4 1 2 4 4.0135939 0.0
     T UP   39(3d) sum 4 5 1 2 3 4.0135939 0.0
     T DOWN 39(3d) sum 3 3 6 7   3.0020503 0.0
     T DOWN 39(3d) sum 3 4 5 7   3.0020503 0.0
     T DOWN 39(3d) sum 3 5 5 6   3.0020503 0.0
   Explanations:
   Row 1-4: Apply a constraint on the sum of the 2nd, 3rd, 4th, and 5th spin-up
            occupation number of the 3d orbital of atom 39 to a target of 4.0135939
   Row 5-7: Apply a constraint on the sum of the 3rd, 4th, and 5th spin-down
            occupation number of the 3d orbital of atom 39 to a target of 3.0020503
   
   Input File:
   &OSCDFT
     oscdft_type=2,
     n_oscdft=20,
     constraint_diag = .true.
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     1 1 1 0.990
     1 1 2 0.990
     1 1 3 0.995
     1 1 4 0.997
     1 1 5 0.997
     1 2 1 0.055
     1 2 2 0.055
     1 2 3 0.171
     1 2 4 0.171
     1 2 5 0.975
     ...
   Explanations:
     Column 1: the atomic index (according to ATOMIC_POSITIONS)
     Column 2: the spin index (1 for up, and 2 for down)
     Column 3: the index of the eigenvalue
               (e.g. from 1 to 5 for d electrons)
     Column 4: the target eignvalue of the occupation matrix
     For more details, see PW/examples/example15/run1 and README.
   
   Input File:
   &OSCDFT
     oscdft_type=2,
     n_oscdft=100,
     constraint_diag = .false.
     ...
   /
   TARGET_OCCUPATION_NUMBERS
     1 1 1 1  1.000
     1 1 1 2  0.000
     1 1 1 3  0.000
     1 1 1 4  0.000
     1 1 1 5  0.000
     1 1 2 1  0.000
     1 1 2 2  1.000
     1 1 2 3  0.000
     1 1 2 4  0.000
     1 1 2 5  0.000
     ...
   Explanations:
     Column 1: the atomic index (according to ATOMIC_POSITIONS)
     Column 2: the spin index (1 for up, and 2 for down)
     Columns 3 and 4: the indices of the magnetic quantum numbers
                      (e.g. from 1 to 5 for d electrons)
     Column 5: the target occupation value
     For more details, see PW/examples/example15/run2 and README.
   

This file has been created by helpdoc utility on Wed Sep 03 14:22:45 CEST 2025
```
