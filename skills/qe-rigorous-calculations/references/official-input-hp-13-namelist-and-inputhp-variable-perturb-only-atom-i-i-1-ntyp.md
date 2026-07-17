# INPUT_HP — NAMELIST: &INPUTHP — Variable: perturb_only_atom(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `af4e0865d080600caf2d959ef977dc790c72fd6ab240b8cd3f2323e47761a2de`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       perturb_only_atom(i), i=1,ntyp
   
   Type:           LOGICAL
   Default:        perturb_only_atom(i) = .false.
   See:            compute_hp
   Description:    If "perturb_only_atom"(i)=.true. then only the i-th
                   atom will be perturbed and considered in the run.
                   This variable is useful when one wants to split
                   the whole calculation on parts.
                   
                   Note: this variable has a higher priority than "skip_type".
   +--------------------------------------------------------------------
   
```
