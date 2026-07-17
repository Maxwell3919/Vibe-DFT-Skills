# INPUT_HP — NAMELIST: &INPUTHP — Variable: sum_pertq

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `6655befeee1f4d8665b923dc289b65c18b9ecc17f353c81fb9c71179401de7a2`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       sum_pertq
   
   Type:           LOGICAL
   Default:        .false.
   See:            start_q, last_q, perturb_only_atom
   Description:    If it is set to .true. then the HP code will collect
                   pieces of the response occupation matrices for all
                   q points. This variable should be used only when
                   "start_q", "last_q" and "perturb_only_atom" are used.
   +--------------------------------------------------------------------
   
```
