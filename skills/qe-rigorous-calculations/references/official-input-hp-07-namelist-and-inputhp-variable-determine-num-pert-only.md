# INPUT_HP — NAMELIST: &INPUTHP — Variable: determine_num_pert_only

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `1fdc92e4b6b72a021f71701f72c467cbbe3c2f363ae1f89e7632177df7f1e190`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       determine_num_pert_only
   
   Type:           LOGICAL
   Default:        .false.
   See:            find_atpert
   Description:    If .true. determines the number of perturbations
                   (i.e. which atoms will be perturbed) and exits smoothly
                   without performing any calculation. For DFT+U+V, it also
                   determines the indices of inter-site couples.
   +--------------------------------------------------------------------
   
```
