# INPUT_PW — CARD: CONSTRAINTS

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d8dc805322f1d067443657ca2ac3d109160caa398c29d587fa17c6ae7c8b0b47`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
CARD: CONSTRAINTS 

   OPTIONAL CARD, USED FOR CONSTRAINED DYNAMICS OR CONSTRAINED OPTIMIZATIONS
   (ONLY IF "ION_DYNAMICS"=='DAMP','VERLET' OR 'VELOCITY-VERLET', VARIABLE-CELL EXCEPTED)
   
   When this card is present the SHAKE algorithm is automatically used.
   
   /////////////////////////////////////////
   // Syntax:                             //
   /////////////////////////////////////////
   
      CONSTRAINTS 
         nconstr { constr_tol }
         constr_type(1)        constr(1)(1)        constr(2)(1)        [  constr(3)(1)        constr(4)(1)        ]  {  constr_target(1)        }  
         constr_type(2)        constr(1)(2)        constr(2)(2)        [  constr(3)(2)        constr(4)(2)        ]  {  constr_target(2)        }  
         . . . 
         constr_type(nconstr)  constr(1)(nconstr)  constr(2)(nconstr)  [  constr(3)(nconstr)  constr(4)(nconstr)  ]  {  constr_target(nconstr)  }  
   
   /////////////////////////////////////////
   
   DESCRIPTION OF ITEMS:
   
      +--------------------------------------------------------------------
      Variable:       nconstr
      
      Type:           INTEGER
      Description:    Number of constraints.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       constr_tol
      
      Type:           REAL
      Description:    Tolerance for keeping the constraints satisfied.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       constr_type
      
      Type:           CHARACTER
      Description:   
                      Type of constraint :
       
                      'type_coord' :
                           constraint on global coordination-number, i.e. the
                           average number of atoms of type B surrounding the
                           atoms of type A. The coordination is defined by
                           using a Fermi-Dirac.
                           (four indexes must be specified).
       
                      'atom_coord' :
                           constraint on local coordination-number, i.e. the
                           average number of atoms of type A surrounding a
                           specific atom. The coordination is defined by
                           using a Fermi-Dirac.
                           (four indexes must be specified).
       
                      'distance' :
                           constraint on interatomic distance
                           (two atom indexes must be specified).
       
                      'planar_angle' :
                           constraint on planar angle
                           (three atom indexes must be specified).
       
                      'torsional_angle' :
                           constraint on torsional angle
                           (four atom indexes must be specified).
       
                      'bennett_proj' :
                           constraint on the projection onto a given direction
                           of the vector defined by the position of one atom
                           minus the center of mass of the others.
                           G. Roma, J.P. Crocombette: J. Nucl. Mater. 403, 32 (2010),
                           doi:10.1016/j.jnucmat.2010.06.001
       
                      'potential_wall' :
                           (experimental) add a potential wall at the origin
                           normal to the the z-axis.
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variables:      constr(1), constr(2), constr(3), constr(4)
      
      Description:    These variables have different meanings for different constraint types:
                      
                      'type_coord' :
                                     constr(1) is the first index of the atomic type involved
                                     constr(2) is the second index of the atomic type involved
                                     constr(3) is the cut-off radius for estimating the coordination
                                     constr(4) is a smoothing parameter
                      
                      'atom_coord' :
                                     constr(1) is the atom index of the atom with constrained coordination
                                     constr(2) is the index of the atomic type involved in the coordination
                                     constr(3) is the cut-off radius for estimating the coordination
                                     constr(4) is a smoothing parameter
                      
                      'distance' :
                                     atoms indices object of the constraint, as they appear in
                                     the "ATOMIC_POSITIONS" card
                      
                      'planar_angle', 'torsional_angle' :
                                     atoms indices object of the constraint, as they appear in the
                                     "ATOMIC_POSITIONS" card (beware the order)
                      
                      'bennett_proj' :
                                     constr(1) is the index of the atom whose position is constrained.
                                     constr(2:4) are the three coordinates of the vector that specifies
                                     the constraint direction.
                      'potential_wall' :
                                     Formula is: External force = prefac * exponent * Exp(-exponent). Force is only applied
                                     on atoms within the cutoff.
                                     constr(1) is the prefactor
                                     constr(2) is the value in the exponent
                                     constr(3) is the cutoff (in a.u.)
      +--------------------------------------------------------------------
      
      +--------------------------------------------------------------------
      Variable:       constr_target
      
      Type:           REAL
      Description:    Target for the constrain ( angles are specified in degrees ).
                      This variable is optional.
      +--------------------------------------------------------------------
      
===END OF CARD==========================================================


========================================================================
```
