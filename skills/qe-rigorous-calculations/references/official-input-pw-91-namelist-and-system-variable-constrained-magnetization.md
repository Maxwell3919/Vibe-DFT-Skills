# INPUT_PW — NAMELIST: &SYSTEM — Variable: constrained_magnetization

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `8078972114433923a260d6b0c839586efb9fc388d20d516ebec7eeb9aa170dad`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       constrained_magnetization
   
   Type:           CHARACTER
   See:            lambda, fixed_magnetization
   Default:        'none'
   Description:   
                   Used to perform constrained calculations in magnetic systems.
                   Currently available choices:
    
                   'none' :
                        no constraint
    
                   'total' :
                        total magnetization is constrained by
                        adding a penalty functional to the total energy:
                        
                        LAMBDA * SUM_{i} ( magnetization(i) - fixed_magnetization(i) )**2
                        
                        where the sum over i runs over the three components of
                        the magnetization. Lambda is a real number (see below).
                        Noncolinear case only. Use "tot_magnetization" for LSDA
    
                   'atomic' :
                        atomic magnetization are constrained to the defined
                        starting magnetization adding a penalty:
                        
                        LAMBDA * SUM_{i,itype} ( magnetic_moment(i,itype) - mcons(i,itype) )**2
                        
                        where i runs over the cartesian components (or just z
                        in the collinear case) and itype over the types (1-ntype).
                        mcons(:,:) array is defined from starting_magnetization,
                        (also from angle1, angle2 in the noncollinear case).
                        lambda is a real number
    
                   'total direction' :
                        the angle theta of the total magnetization
                        with the z axis (theta = fixed_magnetization(3))
                        is constrained:
                        
                        LAMBDA * ( arccos(magnetization(3)/mag_tot) - theta )**2
                        
                        where mag_tot is the modulus of the total magnetization.
    
                   'atomic direction' :
                        not all the components of the atomic
                        magnetic moment are constrained but only the cosine
                        of angle1, and the penalty functional is:
                        
                        LAMBDA * SUM_{itype} ( mag_mom(3,itype)/mag_mom_tot - cos(angle1(ityp)) )**2
    
                   N.B.: symmetrization may prevent to reach the desired orientation
                   of the magnetization. Try not to start with very highly symmetric
                   configurations or use the nosym flag (only as a last remedy)
   +--------------------------------------------------------------------
   
```
