# INPUT_HP — NAMELIST: &INPUTHP — Variable: determine_q_mesh_only

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `6728cc3dc5a7a7755521aaaad29e5645671a0c058226369fc8b4a6f687b5f1b8`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       determine_q_mesh_only
   
   Type:           LOGICAL
   Default:        .false.
   See:            perturb_only_atom
   Description:    If .true. determines the number of q points
                   for a given perturbed atom and exits smoothly.
                   This keyword can be used only if perturb_only_atom
                   is set to .true.
   +--------------------------------------------------------------------
   
```
