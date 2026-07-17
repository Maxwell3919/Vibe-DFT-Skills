# INPUT_PW — NAMELIST: &CELL — Variable: cell_dofree

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `e753601844dacb167f1951636bb82e84ae2e5a49ca59b4964ace9410f375bcc5`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       cell_dofree
   
   Type:           CHARACTER
   Default:        'all'
   Description:   
                   Select which of the cell parameters should be moved:
    
                   'all' :
                        all axis and angles are moved
    
                   'ibrav' :
                        all axis and angles are moved,
                                       but the lattice remains consistent
                                       with the initial ibrav choice. You can use this option in combination
                                       with any other one by specifying "ibrav+option". Please note that some
                                       combinations do not make sense for some crystals and will guarantee that
                                       the relax will never converge. E.g. 'ibrav+2Dxy' is not a problem for
                                       hexagonal cells, but will never converge for cubic ones.
    
                   'a' :
                        the x component of axis 1 (v1_x) is fixed
    
                   'b' :
                        the y component of axis 2 (v2_y) is fixed
    
                   'c' :
                        the z component of axis 3 (v3_z) is fixed
    
                   'fixa' :
                        axis 1 (v1_x,v1_y,v1_z) is fixed
    
                   'fixb' :
                        axis 2 (v2_x,v2_y,v2_z) is fixed
    
                   'fixc' :
                        axis 3 (v3_x,v3_y,v3_z) is fixed
    
                   'x' :
                        only the x component of axis 1 (v1_x) is moved
    
                   'y' :
                        only the y component of axis 2 (v2_y) is moved
    
                   'z' :
                        only the z component of axis 3 (v3_z) is moved
    
                   'xy' :
                        only v1_x and v2_y are moved
    
                   'xz' :
                        only v1_x and v3_z are moved
    
                   'yz' :
                        only v2_y and v3_z are moved
    
                   'xyz' :
                        only v1_x, v2_y, v3_z are moved
    
                   'shape' :
                        all axis and angles, keeping the volume fixed
    
                   'volume' :
                        the volume changes, keeping all angles fixed (i.e. only celldm(1) changes)
    
                   '2Dxy' :
                        only x and y components are allowed to change
    
                   '2Dshape' :
                        as above, keeping the area in xy plane fixed
    
                   'epitaxial_ab' :
                        fix axis 1 and 2 while allowing axis 3 to move
    
                   'epitaxial_ac' :
                        fix axis 1 and 3 while allowing axis 2 to move
    
                   'epitaxial_bc' :
                        fix axis 2 and 3 while allowing axis 1 to move
    
                   BEWARE: if axis are not orthogonal, some of these options do not
                           work (symmetry is broken). If you are not happy with them,
                           edit subroutine init_dofree in file Modules/cell_base.f90
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
