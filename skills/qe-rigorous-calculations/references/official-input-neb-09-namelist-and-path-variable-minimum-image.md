# INPUT_NEB — NAMELIST: &PATH — Variable: minimum_image

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `21cc19f2c6c7beaf1d5528a93b78c3d77b93551de9b223569b181f79cf762d4d`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       minimum_image
         
         Type:           LOGICAL
         Default:        .FALSE.
         Description:    Assume a "minimum image criterion" to build the path. If an atom
                         moves by more than half the length of a crystal axis between one
                         image and the next in the input (before interpolation),
                         an appropriate periodic replica of that atom is chosen.
                         Useful to avoid jumps in the initial reaction path.
         +--------------------------------------------------------------------
         
```
