# INPUT_PW — CARD: ATOMIC_POSITIONS { alat | bohr | angstrom | crystal | crystal_sg }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `4167040303348cb75878c5cea8e04a1e5252ad0a7bab1515a0235084f088fcab`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_POSITIONS { alat | bohr | angstrom | crystal | crystal_sg }

   ________________________________________________________________________
   * IF calculation == 'bands' OR calculation == 'nscf' : 
   
      Specified atomic positions will be IGNORED and those from the
      previous scf calculation will be used instead !!!
      
       
   * ELSE : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         ATOMIC_POSITIONS { alat | bohr | angstrom | crystal | crystal_sg }
            X(1)    x(1)    y(1)    z(1)    {  if_pos(1)(1)    if_pos(2)(1)    if_pos(3)(1)    }  
            X(2)    x(2)    y(2)    z(2)    {  if_pos(1)(2)    if_pos(2)(2)    if_pos(3)(2)    }  
            . . . 
            X(nat)  x(nat)  y(nat)  z(nat)  {  if_pos(1)(nat)  if_pos(2)(nat)  if_pos(3)(nat)  }  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { alat | bohr | angstrom | crystal | crystal_sg }
      
      Default:        (DEPRECATED) alat
      Description:   
                      Units for ATOMIC_POSITIONS:
       
                      alat :
                           atomic positions are in cartesian coordinates, in
                           units of the lattice parameter (either celldm(1)
                           or A). If no option is specified, 'alat' is assumed;
                           not specifying units is DEPRECATED and will no
                           longer be allowed in the future
       
                      bohr :
                           atomic positions are in cartesian coordinate,
                           in atomic units (i.e. Bohr radii)
       
                      angstrom :
                           atomic positions are in cartesian coordinates, in Angstrom
       
                      crystal :
                           atomic positions are in crystal coordinates, i.e.
                           in relative coordinates of the primitive lattice
                           vectors as defined either in card "CELL_PARAMETERS"
                           or via the ibrav + celldm / a,b,c... variables
       
                      crystal_sg :
                           atomic positions are in crystal coordinates, i.e.
                           in relative coordinates of the primitive lattice.
                           This option differs from the previous one because
                           in this case only the symmetry inequivalent atoms
                           are given. The variable "space_group" must indicate
                           the space group number used to find the symmetry
                           equivalent atoms. The other variables that control
                           this option are uniqueb, origin_choice, and
                           rhombohedral.
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variable:       X
      
      Type:           CHARACTER
      Description:    label of the atom as specified in "ATOMIC_SPECIES"
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      x, y, z
      
      Type:           REAL
      Description:    atomic positions
                      
                      NOTE: each atomic coordinate can also be specified as a simple algebraic expression.
                            To be interpreted correctly expression must NOT contain any blank
                            space and must NOT start with a "+" sign. The available expressions are:
                      
                              + (plus), - (minus), / (division), * (multiplication), ^ (power)
                      
                            All numerical constants included are considered as double-precision numbers;
                            i.e. 1/2 is 0.5, not zero. Other functions, such as sin, sqrt or exp are
                            not available, although sqrt can be replaced with ^(1/2).
                      
                            Example:
                                  C  1/3   1/2*3^(-1/2)   0
                      
                            is equivalent to
                      
                                  C  0.333333  0.288675  0.000000
                      
                            Please note that this feature is NOT supported by XCrysDen (which will
                            display a wrong structure, or nothing at all).
                      
                            When atomic positions are of type crystal_sg coordinates can be given
                            in the following four forms (Wyckoff positions):
                               C  1a
                               C  8g   x
                               C  24m  x y
                               C  48n  x y z
                            The first form must be used when the Wyckoff letter determines uniquely
                            all three coordinates, forms 2,3,4 when the Wyckoff letter and 1,2,3
                            coordinates respectively are needed.
                      
                            The forms:
                               C 8g  x  x  x
                               C 24m x  x  y
                            are not allowed, but
                               C x x x
                               C x x y
                               C x y z
                            are correct.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      if_pos(1), if_pos(2), if_pos(3)
      
      Type:           INTEGER
      Default:        1
      Description:    component i of the force for this atom is multiplied by if_pos(i),
                      which must be either 0 or 1.  Used to keep selected atoms and/or
                      selected components fixed in MD dynamics or
                      structural optimization run.
                      
                      With crystal_sg atomic coordinates the constraints are copied in all equivalent
                      atoms.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
