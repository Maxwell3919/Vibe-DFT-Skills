# INPUT_CP — CARD: ATOMIC_POSITIONS { alat | bohr | angstrom | crystal }

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `34cdfdda3a3c680d39d561c20af5714597a9259496342032d0755a13ab732d52`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: ATOMIC_POSITIONS { alat | bohr | angstrom | crystal }

   ________________________________________________________________________
   * IF calculation == 'bands' OR calculation == 'nscf' : 
   
      Specified atomic positions will be IGNORED and those from the
      previous scf calculation will be used instead !!!
      
       
   * ELSE IF  : 
   
      /////////////////////////////////////////
      // Syntax:                             //
      /////////////////////////////////////////
      
         ATOMIC_POSITIONS { alat | bohr | angstrom | crystal }
            X(1)    x(1)    y(1)    z(1)    {  if_pos(1)(1)    if_pos(2)(1)    if_pos(3)(1)    }  
            X(2)    x(2)    y(2)    z(2)    {  if_pos(1)(2)    if_pos(2)(2)    if_pos(3)(2)    }  
            . . . 
            X(nat)  x(nat)  y(nat)  z(nat)  {  if_pos(1)(nat)  if_pos(2)(nat)  if_pos(3)(nat)  }  
      
      /////////////////////////////////////////
      
       
   ENDIF
   ________________________________________________________________________
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Card's flags:   { alat | bohr | angstrom | crystal }
      
      Default:        (DEPRECATED) bohr
      Description:    alat    : atomic positions are in cartesian coordinates,
                                in units of the lattice parameter (either
                                celldm(1) or A).
                      
                      bohr    : atomic positions are in cartesian coordinate,
                                in atomic units (i.e. Bohr).
                                If no option is specified, 'bohr' is assumed;
                                not specifying units is DEPRECATED and will no
                                longer be allowed in the future
                      
                      angstrom: atomic positions are in cartesian coordinates,
                                in Angstrom
                      
                      crystal : atomic positions are in crystal coordinates, i.e.
                                in relative coordinates of the primitive lattice
                                vectors as defined either in card CELL_PARAMETERS
                                or via the ibrav + celldm / a,b,c... variables
      +--------------------------------------------------------------------


      +--------------------------------------------------------------------
      Variable:       X
      
      Type:           CHARACTER
      Description:    label of the atom as specified in ATOMIC_SPECIES
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      x, y, z
      
      Type:           REAL
      Description:    atomic positions
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      if_pos(1), if_pos(2), if_pos(3)
      
      Type:           INTEGER
      Default:        1
      Description:    component i of the force for this atom is multiplied by if_pos(i),
                      which must be either 0 or 1.  Used to keep selected atoms and/or
                      selected components fixed in MD dynamics or
                      structural optimization run.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
