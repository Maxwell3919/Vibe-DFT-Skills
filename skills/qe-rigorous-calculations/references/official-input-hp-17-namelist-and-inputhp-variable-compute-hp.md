# INPUT_HP — NAMELIST: &INPUTHP — Variable: compute_hp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `60f03ab23823f35c7adf20a81bc6cc967eba3483a02f8dc6d56e9e9875887b8f`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       compute_hp
   
   Type:           LOGICAL
   Default:        .false.
   See:            perturb_only_atom
   Description:    If it is set to .true. then the HP code will collect
                   pieces of the chi0 and chi matrices (which must have
                   been produced in previous runs) and then compute
                   Hubbard parameters. The HP code will look for files
                   tmp_dir/HP/prefix.chi.i.dat. Note that all files
                   prefix.chi.i.dat (where i runs over all perturbed
                   atoms) must be placed in one folder tmp_dir/HP/.
                   "compute_hp"=.true. must be used only when the
                   calculation was parallelized over perturbations.
   +--------------------------------------------------------------------
   
```
