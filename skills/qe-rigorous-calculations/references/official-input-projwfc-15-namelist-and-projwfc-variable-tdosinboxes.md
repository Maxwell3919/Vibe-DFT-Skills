# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: tdosinboxes

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `214c8f5c16ff8fa1b3eedacb16259b60c0517aa647f195e8d5fa2ce5f979e9af`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tdosinboxes
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true. compute the local DOS integrated in volumes
                   
                   Volumes are defined as boxes with edges parallel to the unit cell,
                   containing the points of the (charge density) FFT grid included within
                   "irmin" and "irmax", in the three dimensions:
                   
                   from "irmin"(j,n) to "irmax"(j,n) for j=1,2,3 (n=1,"n_proj_boxes").
   +--------------------------------------------------------------------
   
```
