# INPUT_PW — NAMELIST: &SYSTEM — Variable: nosym_evc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `276227cf608523e1e9f3a095d548ec37d9e48ea4ecd3aec3bb2a6ef0d73e3150`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nosym_evc
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    if (.TRUE.) symmetry is not used, and k points are
                   forced to have the symmetry of the Bravais lattice;
                   an automatically generated Monkhorst-Pack grid will contain
                   all points of the grid over the entire Brillouin Zone,
                   plus the points rotated by the symmetries of the Bravais
                   lattice which were not in the original grid. The same
                   applies if a k-point list is provided in input instead
                   of a Monkhorst-Pack grid. Time reversal symmetry is assumed
                   so k and -k are equivalent unless "noinv"=.true. is specified.
                   This option differs from "nosym" because it forces k-points
                   in all cases to have the full symmetry of the Bravais lattice
                   (not all uniform grids have such property!)
   +--------------------------------------------------------------------
   
```
