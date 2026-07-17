# INPUT_PW — NAMELIST: &CELL — Variable: cell_factor

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `04ff8a27c3116868a9e2080a6e1bc2558ceb2c5b5684ebdc0350f018865c2b07`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       cell_factor
   
   Type:           REAL
   Default:        2.0 for variable-cell calculations, 1.0 otherwise
   Description:    Used in the construction of the pseudopotential tables.
                   It should exceed the maximum linear contraction of the
                   cell during a simulation.
   +--------------------------------------------------------------------
   
```
