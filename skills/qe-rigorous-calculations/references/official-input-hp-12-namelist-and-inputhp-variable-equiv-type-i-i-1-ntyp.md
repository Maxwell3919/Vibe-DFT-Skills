# INPUT_HP — NAMELIST: &INPUTHP — Variable: equiv_type(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `2a32036d19998ae2fb044e69d5134d3cd27ed225607a25bf42989357d4e39709`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       equiv_type(i), i=1,ntyp
   
   Type:           INTEGER
   Default:        equiv_type(i) = 0
   See:            skip_type
   Description:    "equiv_type"(i), where i runs over types of atoms.
                   "equiv_type"(i)=j, will make type i equivalent to type j
                   (useful when nspin=2). Such a merging of types is done
                   only at the post-processing stage.
                   This keyword cannot be used when "find_atpert" = 1.
   +--------------------------------------------------------------------
   
```
