# INPUT_PW — NAMELIST: &RISM — Variable: laue_starting_right

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d3b0206af6f984fb54c69e4bd28cb5a6f87c5217496ebebe910e233a3184969c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       laue_starting_right
   
   Type:           REAL
   Default:        0.0
   Description:    Set the starting position [in a.u.] of the solvent region
                   on right-hand side of the unit cell. Then the solvent region is
                   defined as [ "laue_starting_right" , L_z/2 + "laue_expand_right" ],
                   where distribution functions are finite.
                   This is only for Laue-RISM.
   +--------------------------------------------------------------------
   
```
