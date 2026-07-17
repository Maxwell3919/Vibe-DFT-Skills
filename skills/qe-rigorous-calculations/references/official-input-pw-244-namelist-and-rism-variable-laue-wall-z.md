# INPUT_PW — NAMELIST: &RISM — Variable: laue_wall_z

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `0267945db25bdd8c4849cb6a620c02943d2f60c5099bb160653f3abfe200c67b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       laue_wall_z
   
   Type:           REAL
   Default:        0.0
   Description:    Set the edge position [in a.u.] of the repulsive wall.
                   If "laue_expand_right" > 0.0, the repulsive wall is defined on [ -inf , "laue_wall_z" ].
                   If "laue_expand_left" > 0.0, the repulsive wall is defined on [ "laue_wall_z" , inf ].
                   This is only for Laue-RISM and "laue_wall" == 'manual' .
   +--------------------------------------------------------------------
   
```
