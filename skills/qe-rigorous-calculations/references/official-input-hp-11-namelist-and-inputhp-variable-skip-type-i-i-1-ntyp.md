# INPUT_HP — NAMELIST: &INPUTHP — Variable: skip_type(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `c490f1f3f4696c1125e47ecfb12cfba410731f5a1c95fc75e477aa51fb37ca7d`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       skip_type(i), i=1,ntyp
   
   Type:           LOGICAL
   Default:        skip_type(i) = .false.
   See:            equiv_type
   Description:    "skip_type"(i), where i runs over types of atoms.
                   If "skip_type"(i)=.true. then no linear-response
                   calculation will be performed for the i-th atomic type:
                   in this case "equiv_type"(i) must be specified, otherwise
                   the HP code will stop. This option is useful if the
                   system has atoms of the same type but opposite spin
                   pollarizations (anti-ferromagnetic case).
                   This keyword cannot be used when "find_atpert" = 1.
   +--------------------------------------------------------------------
   
```
