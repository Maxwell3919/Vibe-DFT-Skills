# INPUT_PW — NAMELIST: &RISM — Variable: laue_buffer_left

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `444a9683bd165b89be125435a4cf8011c0e6514f12814d4e48105b2701eb3521`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       laue_buffer_left
   
   Type:           REAL
   Default:        8.0 if "laue_expand_left" > 0.0;
                   -1.0 if "laue_expand_left" <= 0.0
   Description:    If positive value, set the buffering length [in a.u.]
                   of the solvent region on left-hand side of the unit cell.
                   Then correlation functions are defined inside of
                   [ -L_z/2 - "laue_expand_left" , "laue_starting_left" + "laue_buffer_left" ].
                   This is only for Laue-RISM.
   +--------------------------------------------------------------------
   
```
