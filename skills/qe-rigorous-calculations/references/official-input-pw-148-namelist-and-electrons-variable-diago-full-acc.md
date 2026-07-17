# INPUT_PW — NAMELIST: &ELECTRONS — Variable: diago_full_acc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `6c64cf850b029445ee23c809863fabb432970e468a1936336c7642a6d74868d0`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       diago_full_acc
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. all the empty states are diagonalized at the same level
                   of accuracy of the occupied ones. Otherwise the empty states are
                   diagonalized using a larger threshold (this should not affect
                   total energy, forces, and other ground-state properties).
   +--------------------------------------------------------------------
   
```
