# INPUT_NEB — NAMELIST: &PATH — Variable: use_freezing

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `399025dc2b07ad8c2863bda0c5573e4da912848fb5642f6a7a8076a7d8bdee6f`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       use_freezing
         
         Type:           LOGICAL
         Default:        .FALSE.
         Description:    If. TRUE. the images are optimised according to their error:
                         only those images with an error larger than half of the largest
                         are optimised. The other images are kept frozen.
         +--------------------------------------------------------------------
         
```
