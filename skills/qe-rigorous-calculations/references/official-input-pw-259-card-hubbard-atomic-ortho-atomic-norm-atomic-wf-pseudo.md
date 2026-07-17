# INPUT_PW — CARD: HUBBARD atomic | ortho-atomic | norm-atomic | wf | pseudo

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `47b9cd42cd0e2fc90837d758422b07f0de0e78d17f46c9b8aeab2012239bdf31`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: HUBBARD atomic | ortho-atomic | norm-atomic | wf | pseudo

   ________________________________________________________________________
   * IF DFT+U : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         HUBBARD  atomic | ortho-atomic | norm-atomic | wf | pseudo 
            U label(1)-manifold(1) u_val(1)
            [ ALPHA label(1)-manifold(1) alpha_val(1) ]
            [ J0 label(1)-manifold(1) j0_val(1) ]
            . . .
            U label(n)-manifold(n) u_val(n)
            [ ALPHA label(n)-manifold(n) alpha_val(n) ]
            [ J0 label(n)-manifold(n) j0_val(n) ]
      
      /////////////////////////////////////////
      
       
   * ELSE IF DFT+U+J : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         HUBBARD  atomic | ortho-atomic | norm-atomic | wf | pseudo 
            paramType(1) label(1)-manifold(1) paramValue(1)
            . . .
            paramType(n) label(n)-manifold(n) paramValue(n)
      
      /////////////////////////////////////////
      
       
   * ELSE IF DFT+U+V : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         HUBBARD  atomic | ortho-atomic | norm-atomic | wf | pseudo 
            U label(I)-manifold(I) u_val(I)
            [ J0 label(I)-manifold(I) j0_val(I) ]
            V label(I)-manifold(I) label(J)-manifold(J) I J v_val(I,J)
            . . .
            U label(N)-manifold(N) u_val(N)
            [ J0 label(N)-manifold(N) j0_val(N) ]
            V label(N)-manifold(N) label(M)-manifold(M) N M v_val(N,M)
      
      /////////////////////////////////////////
      
       
   * ELSE IF DFT+U (orbital-resolved) : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         HUBBARD  atomic | ortho-atomic | norm-atomic | wf | pseudo 
            U label(1)-shell(1) u_val(1) eigenstate(1,m)
            [ ALPHA label(1)-shell(1) alpha_val(1) eigenstate(1,m) ]
            . . .
            U label(n)-shell(n) u_val(n) eigenstate(n,m)
            [ ALPHA label(n)-shell(n) alpha_val(n) eigenstate(n,m) ]
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   atomic | ortho-atomic | norm-atomic | wf | pseudo
      
      Description:   
                      HUBBARD options are:
       
                      atomic :
                           use atomic orbitals (read from pseudopotential) to build the
                           Hubbard projectors
       
                      ortho-atomic :
                           use Lowdin orthogonalized atomic orbitals. This option is
                           recommended to be used whenever possible instead of atomic
                           because it allows to avoid applying Hubbard corrections twice
                           in the orbital overlap regions.
       
                      norm-atomic :
                           Lowdin normalization of atomic orbitals. Keep in mind:
                           atomic orbitals are not orthogonalized in this case.
                           This is a "quick and dirty" trick to be used when
                           atomic orbitals from the pseudopotential are not
                           normalized (and thus produce occupation whose
                           value exceeds unity).
       
                      wf :
                           use Wannier functions to built Hubbard projectors.
                           The information about the Wannier functionas are read
                           from file "prefix".hub that must be generated using pmw.x
                           (see PP/src/poormanwannier.f90 for details).
                           Note: these are not maximally localized Wannier functions.
                           (see PP/examples/example05)
       
                      pseudo :
                           use the pseudopotential projectors. The charge density
                           outside the atomic core radii is excluded.
                           N.B.: for atoms with +U, a pseudopotential with the
                           all-electron atomic orbitals are required (i.e.,
                           as generated by ld1.x with lsave_wfc flag).
       
                      NB: forces and stress are currently implemented only for the
                      'atomic', 'ortho-atomic', and 'pseudo' Hubbard projectors.
       
                      Check Doc/Hubbard_input.pdf to see how to specify Hubbard parameters
                      U, ALPHA, J0, J, B, E2, E3, V in the HUBBARD card.
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variables:      label(1)-manifold(1), u_val(1)
      
      Type:           CHARACTER-LITERAL, CHARACTER, REAL
      Description:    Syntax:
                        U label-manifold u_val
                      
                      Where:
                      U        = string constant "U"; indicates the specs for the U parameter will be given
                      label    = label of the atom (as defined in "ATOMIC_SPECIES")
                      manifold = specs of the manifold (e.g., 3d, 2p...)
                      u_val    = value of the U parameter (in eV)
                      
                      Example:
                      HUBBARD (ortho-atomic)
                        U Mn-3d 5.0
                        U Ni-3d 6.0
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(1)-manifold(1), alpha_val(1)
      
      Type:           CHARACTER-LITERAL, CHARACTER, REAL
      Description:    Remark: specs of ALPHA parameters are optional
                      ALPHA is the perturbation used to compute U (and V) with the linear-response method of
                      Cococcioni and de Gironcoli, PRB 71, 035105 (2005).
                      
                      Syntax:
                        ALPHA label-manifold alpha_val
                      
                      Where:
                      ALPHA     = string constant "ALPHA"; indicates that specs for the ALPHA parameter will be given
                      label     = label of the atom (as defined in "ATOMIC_SPECIES")
                      manifold  = specs of the manifold (e.g., 3d, 2p...)
                      alpha_val = value of the ALPHA parameter (in eV)
                      
                      Example:
                        HUBBARD (ortho-atomic)
                        U     Ni-3d 5.00
                        ALPHA Ni-3d 0.05
                        U     Mn-3d 5.00
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(1)-manifold(1), j0_val(1)
      
      Type:           CHARACTER-LITERAL, CHARACTER, REAL
      Description:    Remark: specs of J0 parameters are optional
                      
                      Syntax:
                        J0 label-manifold j0_val
                      
                      Where:
                      J0       = string constant "J0"; indicates the specs for the J0 parameter will be given
                      label    = label of the atom (as defined in "ATOMIC_SPECIES")
                      manifold = specs of the manifold (e.g., 3d, 2p...)
                      j0_val   = value of the J0 parameter (in eV)
                      
                      Example:
                        HUBBARD (ortho-atomic)
                        U  Mn-3d 5.0
                        J0 Mn-3d 1.0
                        U  Ni-3d 6.0
                        J0 Ni-3d 1.2
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      paramType(1), label(1)-manifold(1), paramValue(1)
      
      Type:           CHARACTER, CHARACTER, REAL
      Description:    Syntax of the line:
                      
                        paramType label-manifold paramValue
                      
                      Where:
                      paramType  = character describing the type of Hubbard parameter
                                   allowed values: U, J and either B (for d-orbitals) or E2 and E3 (for f-orbitals)
                      label      = label of the atom (as defined in "ATOMIC_SPECIES")
                      manifold   = specs of the manifold (e.g., 3d, 2p...)
                      paramValue = value of the parameter (in eV)
                      
                      Example:
                        HUBBARD (ortho-atomic)
                        U Mn-3d 5.0
                        J Mn-3d 1.0
                        B Mn-3d 1.1
                        U Ni-3d 6.0
                        J Ni-3d 1.2
                        B Ni-3d 1.3
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(I)-manifold(I), u_val(I)
      
      Type:           CHARACTER, REAL
      Description:    Syntax of the line:
                      
                        U label-manifold u_val
                      
                      Where:
                      U        = string constant "U"; indicates the specs for the U parameter will be given
                      label    = label of the atom (as defined in "ATOMIC_SPECIES")
                      manifold = specs of the manifold (e.g., 3d, 2p...)
                      u_val    = value of the U parameter (in eV)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(I)-manifold(I), j0_val(I)
      
      Type:           CHARACTER, REAL
      Description:    Remark: specs of J0 parameters are optional
                      
                      Syntax of the line:
                      
                        J0 label(I)-manifold(I) j0_val(I)
                      
                      Where:
                      J0       = string constant "J0"; indicates the specs for the J0 parameter will be given
                      label    = label of the atom (as defined in "ATOMIC_SPECIES")
                      manifold = specs of the manifold (e.g., 3d, 2p...)
                      j0_val   = value of the J0 parameter (in eV)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(I)-manifold(I), label(J)-manifold(J), I, J, v_val(I,J)
      
      Type:           CHARACTER, CHARACTER, INTEGER, INTEGER, REAL
      Description:    Syntax of the line:
                      
                        V label(I)-manifold(J) label(J)-manifold(J) I J v_val(I,J)
                      
                      Where:
                      V           = string constant "V"; indicates the specs for the V parameter will be given
                      label(I)    = label of the atom I (as defined in "ATOMIC_SPECIES")
                      manifold(I) = specs of the manifold for atom I (e.g., 3d, 2p...)
                      label(J)    = label of the atom J (as defined in "ATOMIC_SPECIES")
                      manifold(J) = specs of the manifold for atom J (e.g., 3d, 2p...)
                      I           = index of the atom I
                      J           = index of the atom J
                      v_val(I,J)  = value of the V parameter for the atom pair I,J (in eV)
                      
                      Example:
                        HUBBARD (ortho-atomic)
                        U Co-3d 7.70
                        V Co-3d O-2p 1 19 0.75
                        V Co-3d O-2p 1 46 0.75
                        V Co-3d O-2p 1 43 0.75
                        V Co-3d O-2p 1 54 0.75
                        V Co-3d O-2p 1 11 0.75
                        V Co-3d O-2p 1 22 0.75
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(1)-shell(1), u_val(1), eigenstate(1,m)
      
      Type:           CHARACTER-LITERAL, CHARACTER, REAL, INTEGER
      Description:    Syntax of the eigenstate parameter:
                      
                      CASE ( "nspin" == 1 ):
                          Provide one up to 2l+1 (e.g., 5 for a d-shell) eigenstate indices varying
                          between 1 and 2l+1.
                          These values correspond to the m-th eigenstate(s) of the shell occupancy
                          matrix, to be targeted by Hubbard U corrections (see PW/examples/example15).
                      
                          Example:
                              HUBBARD (ortho-atomic)
                              U Mn-3d 4.70  3 4 5
                              U Ni-3d 3.50  1 2
                      
                      CASE ( "nspin" == 2 ):
                          Provide one up to 2*(2l+1) (e.g., 10 for a d-shell) eigenstate indices varying
                          between 1 and 2*(2l+1). These values correspond to the m-th eigenstate(s) of
                          the shell collinear occupancy matrix, to be targeted by Hubbard U corrections.
                          Indices from 1 to 2l+1 target spin-up eigenstates, while those from (2l+2)
                          to 2*(2l+1) target the  spin-down ones (see PW/examples/example16).
                      
                          Example:
                              HUBBARD (ortho-atomic)
                              U Mn-3d 4.70  3 4 5 8 9 10
                              U Ni-3d 3.50  1 2 6 7
                      
                      CASE ( "noncolin" = .true. ):
                          Provide one up to 2*(2l+1) (e.g., 10 for a d-shell) eigenstate indices varying
                          between 1 and 2*(2l+1). These values correspond to the m-th eigenstate(s) of
                          the noncollinear occupancy matrix of the shell, to be targeted by Hubbard U
                          corrections.
                      
                          Example:
                              HUBBARD (ortho-atomic)
                              U Mn-3d 4.70  3 4 5 8 9 10
                              U Ni-3d 3.50  1 2 6 7
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      label(1)-shell(1), alpha_val(1), eigenstate(1,m)
      
      Type:           CHARACTER-LITERAL, CHARACTER, REAL, INTEGER
      Description:    Remark: specs of (orbital-resolved) ALPHA parameters are optional
                      ALPHA is the perturbation used to compute U with the orbital-resolved
                      linear-response method of Macke et al., arXiv:2312.13580 (2023), based on
                      Cococcioni and de Gironcoli, PRB 71, 035105 (2005).
                      
                      Syntax of the line:
                      ALPHA label-shell alpha_val eigenstate(1) [... eigenstate(m)]
                      
                      Where:
                      ALPHA         = string constant "ALPHA"; indicates that specs for an ALPHA parameter will be given
                      label         = label of the atom (as defined in "ATOMIC_SPECIES")
                      shell         = specs of the nl-subshell (e.g., 3d, 2p...)
                      alpha_val     = value of the ALPHA parameter (in eV)
                      eigenstate(m) = index/indices of the m-th eigenstate(s) belonging to the shell
                                         that will be targeted by ALPHA (same syntax as for orbital-resolved
                                         Hubbard U)
                      
                      Example:
                          HUBBARD (ortho-atomic)
                          U     Mn-3d 4.70 3 4 5
                          U     Ni-3d 3.50 1 2
                          ALPHA Ni-3d 0.05 1 2
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


This file has been created by helpdoc utility on Wed Sep 03 14:22:44 CEST 2025
```
