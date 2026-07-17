# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: irmax(i,n_proj_boxes), (i,n_proj_boxes)=(1,1) ... (3,n_proj_boxes)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `df951a0c5d41eb8c21219261dd99c467b314f828c8578619453c6b3436fb55ca`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       irmax(i,n_proj_boxes), (i,n_proj_boxes)=(1,1) ... (3,n_proj_boxes)
   
   Type:           INTEGER
   Default:        0 for each box
   Description:    last point of the given box;
                   ( 0 stands for the last point in the FFT grid )
                   
                   BEWARE: "irmax" is a 2D array of the form: "irmax"(3,"n_proj_boxes")
   +--------------------------------------------------------------------
   
```
