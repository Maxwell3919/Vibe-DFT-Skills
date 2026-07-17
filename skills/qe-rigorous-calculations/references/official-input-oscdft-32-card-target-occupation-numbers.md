# INPUT_OSCDFT — CARD: TARGET_OCCUPATION_NUMBERS

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `5ec3bdcbb50d1dd93d0c2799aa1bb47fba3317e7e139e5f6ab816d1a75007974`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: TARGET_OCCUPATION_NUMBERS 

   SPECIFIES THE OS-CDFT CONSTRAINT TO APPLY.
   ALSO ALLOWS PRINTING OF OCCUPATION MATRIX WITHOUT APPLYING OS-CDFT CONSTRAINTS.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      TARGET_OCCUPATION_NUMBERS 
         applied(1)         spin(1)         orbital_desc(1)         [  constr_idx(1)         target(1)         start_mul(1)         {  start_index(1)         }  ]  
         applied(2)         spin(2)         orbital_desc(2)         [  constr_idx(2)         target(2)         start_mul(2)         {  start_index(2)         }  ]  
         . . . 
         applied(n_oscdft)  spin(n_oscdft)  orbital_desc(n_oscdft)  [  constr_idx(n_oscdft)  target(n_oscdft)  start_mul(n_oscdft)  {  start_index(n_oscdft)  }  ]  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       applied
      
      Type:           CHARACTER
      Status:         REQUIRED
      Description:   
                      T :
                           Applies a constraint.
                           
                           "spin", "orbital_desc", "constr_idx", "target",
                           and "start_mul" are requried.
                           "spin" is optional.
       
                      F :
                           Just prints the occupation number.
                           
                           Only "spin" and "orbital_desc" are requried.
                           Others are ignored.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       spin
      
      Type:           CHARACTER
      Status:         REQUIRED
      Description:   
                      1, UP  :
                           Spin up channel
       
                      2, DOWN  :
                           Spin down channel
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       orbital_desc
      
      Type:           CHARACTER
      Status:         REQUIRED
      Description:    Orbitals included in the occupation number
                      
                      Syntax of the orbital descriptor:
                           atom_index(manifold...)...
                      
                      Where:
                      atom_index = atom index in the order of ATOMIC_POSITIONS
                      manifold   = principal and azimuthal quantum numbers
                                      (can specify more than one manifolds)
                                      (eg. 3d, 2s2p)
                      
                      Examples:
                      5(3d)   describes a 5x5 occupation matrix which includes:
                      - 3d orbital of atom 5.
                      
                      3(2s2p) describes a 4x4 occupation matrix which includes:
                      - 2s orbital of atom 3.
                      - 2p orbital of atom 3.
                      
                      Additional notes: See ADDITIONAL NOTES below.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       constr_idx
      
      Type:           VARIOUS
      Status:         REQUIRED if "applied"(I) == T
      Description:    Specifies how the constraint is applied:
                      
                      To apply a constraint on an occupation number:
                        Write the index of the occupation numbers, sorted in ascending order,
                        where the OS-CDFT constraint is applied.
                        See "swapping_technique".
                      
                        Example:
                        Apply a constraint to the 5th spin-up occupation number of
                        the 3d orbital of atom 2 to a target of 0.9
                        &OSCDFT
                          n_oscdft=1
                          ...
                        /
                        TARGET_OCCUPATION_NUMBERS
                          T UP 2(3d) 5 0.9 0.0
                      
                      To apply a constraint on the trace of the occupation matrix:
                        Write trace for this variable.
                        "swapping_technique" is ignored when this is used.
                      
                        Example:
                        Apply a constraint to the trace of the spin-up occupation number of
                        the 3d orbital of atom 2 to a target of 3.2
                        &OSCDFT
                          n_oscdft=1
                          ...
                        /
                        TARGET_OCCUPATION_NUMBERS
                          T UP 2(3d) trace 3.2 0.0
                      
                      To apply a cosntraint on the sum of occupation numbers:
                        sum number orbital_index row_index(1) ... row_index(number-1)
                        Applies constraint on orbital_index-th occupation number
                        of the occupation matrix.
                        However, the occupation number inputted to the optimization subroutines
                        is the sum of this orbital index along with the occupation number of
                        row_index(1) ... row_index(number-1)
                        "swapping_technique" is ignored when this is used.
                      
                        Example:
                        Apply a constraint to the sum of the 3rd, 4th, and 5th
                        occupation numbers of the 3d orbital of atom 2 to a target of 2.8
                        &OSCDFT
                          n_oscdft=3
                          ...
                        /
                        TARGET_OCCUPATION_NUMBERS
                          T UP 2(3d) sum 3 3 2 3 2.8 0.0
                          T UP 2(3d) sum 3 4 1 3 2.8 0.0
                          T UP 2(3d) sum 3 5 1 2 2.8 0.0
                      
                        Explanation:
                        Row 1: Applies constraint to 3rd occupation number. However, the multiplier is
                               optimized until the sum of the 3rd occupation number, along with the
                               occupation numbers of row 2 and row 3 of the "TARGET_OCCUPATION_NUMBERS"
                               card equals 2.8
                        Row 2: Applies constraint to 4th occupation number. However, the multiplier is
                               optimized until the sum of the 4th occupation number, along with the
                               occupation numbers of row 1 and row 3 of the "TARGET_OCCUPATION_NUMBERS"
                               card equals 2.8
                        Row 3: Applies constraint to 5th occupation number. However, the multiplier is
                               optimized until the sum of the 5th occupation number, along with the
                               occupation numbers of row 1 and row 2 of the "TARGET_OCCUPATION_NUMBERS"
                               card equals 2.8
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       target
      
      Type:           DOUBLE
      Status:         REQUIRED if "applied"(I) == T
      Description:    The target occupation number for the constraint.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       start_mul
      
      Type:           DOUBLE
      Status:         REQUIRED if "applied"(I) == T
      Description:    Starting value of the multiplier.
                      For normal operations, set this to 0.D0.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       start_index
      
      Type:           INTEGER
      Default:        1
      Description:    If "iteration_type" is 0, delays the application of this
                      row of OS-CDFT constraint until the rest of the constraint is
                      converged. Otherwise, this is ignored.
                      
                      Example ("n_oscdft" = 4):
                      TARGET_OCCUPATION_NUMBERS
                        T UP 3(3d) 5 0.9 0.0 1
                        T UP 4(3d) 5 0.9 0.0 1
                        T UP 5(3d) 5 0.9 0.0 2
                        T UP 6(3d) 5 0.9 0.0 3
                      The constraints on atom 3 and 4 are applied first until convergence.
                      Then, the constraints on atom 3, 4, and 5 are applied until convergence.
                      Finally, the constraints on atom 3, 4, 5, and 6 are applied until convergence.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
