# INPUT_PW — NAMELIST: &SYSTEM — Variable: esm_bc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `0a4f53b2b566420d7799da268b9aea6376f2b5d4666b8f6c03cb24f3dfb97a41`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       esm_bc
   
   Type:           CHARACTER
   See:            assume_isolated
   Default:        'pbc'
   Description:   
                   If "assume_isolated" = 'esm', determines the boundary
                   conditions used for either side of the slab.
                   
                   Currently available choices:
    
                   'pbc' :
                        (default): regular periodic calculation (no ESM).
    
                   'bc1' :
                        Vacuum-slab-vacuum (open boundary conditions).
    
                   'bc2' :
                        Metal-slab-metal (dual electrode configuration).
                        See also "esm_efield".
    
                   'bc3' :
                        Vacuum-slab-metal
   +--------------------------------------------------------------------
   
```
