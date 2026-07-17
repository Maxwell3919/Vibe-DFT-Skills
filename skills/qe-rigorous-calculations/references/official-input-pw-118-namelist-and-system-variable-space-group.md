# INPUT_PW — NAMELIST: &SYSTEM — Variable: space_group

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `753a383896e3a107dc8d8b9dd0536cd47bf87a17606e108d40bdb8bd12586645`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       space_group
   
   Type:           INTEGER
   Default:        0
   Description:    The number of the space group of the crystal, as given
                   in the International Tables of Crystallography A (ITA).
                   This allows to give in input only the inequivalent atomic
                   positions. The positions of all the symmetry equivalent atoms
                   are calculated by the code. Used only when the atomic positions
                   are of type crystal_sg. See also "uniqueb",
                   "origin_choice", "rhombohedral"
   +--------------------------------------------------------------------
   
```
