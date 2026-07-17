# INPUT_NEB — NAMELIST: &PATH — Variable: CI_scheme

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `e84011f330224779cfe621ea27b019d0578d2566ab517d5284a8f7029315aad7`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       CI_scheme
         
         Type:           CHARACTER
         Default:        'no-CI'
         Description:   
                         Specify the type of Climbing Image scheme:
          
                         'no-CI' :
                              climbing image is not used
          
                         'auto' :
                              original CI scheme. The image highest in energy
                              does not feel the effect of springs and is
                              allowed to climb along the path
          
                         'manual' :
                              images that have to climb are manually selected.
                              See also "CLIMBING_IMAGES" card
         +--------------------------------------------------------------------
         
```
