# INPUT_CP — NAMELIST: &WANNIER — Variable: writev

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `843b8728318df5eee03b00777048af3922a32b29867f6b8a954777f01694d393`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       writev
   
   Type:           LOGICAL
   Default:        .false.
   Description:    Output the charge density (g-space) and the list of g-vectors
                   This is useful if you want to reconstruct the electrostatic
                   potential using the Poisson equation. If .TRUE. then the
                   code will output the g-space charge density and the list
                   if G-vectors, and STOP.
                   Charge density is written to : CH_DEN_G_PARA.ispin (1 or 2
                   depending on the number of spin types) or CH_DEN_G_SERL.ispin
                   depending on if the code is being run in parallel or serial
                   G-vectors are written to G_PARA or G_SERL.
   +--------------------------------------------------------------------
   
```
