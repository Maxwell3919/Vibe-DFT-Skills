# INPUT_CP — NAMELIST: &CELL — Variable: cell_dofree

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `3596ebc007555908863fb4dde7574a1089b27f552d7263d5496d6846af2a9f5b`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       cell_dofree
   
   Type:           CHARACTER
   Default:        'all'
   Description:    Select which of the cell parameters should be moved:
                   
                   all     = all axis and angles are moved
                   x       = only the x component of axis 1 (v1_x) is moved
                   y       = only the y component of axis 2 (v2_y) is moved
                   z       = only the z component of axis 3 (v3_z) is moved
                   xy      = only v1_x and v2_y are moved
                   xz      = only v1_x and v3_z are moved
                   yz      = only v2_y and v3_z are moved
                   xyz     = only v1_x, v2_y, v3_z are moved
                   shape   = all axis and angles, keeping the volume fixed
                   2Dxy    = only x and y components are allowed to change
                   2Dshape = as above, keeping the area in xy plane fixed
                   volume  = isotropic variations of v1_x, v2_y, v3_z, keeping
                             the shape fixed. Should be used only with ibrav=1.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
