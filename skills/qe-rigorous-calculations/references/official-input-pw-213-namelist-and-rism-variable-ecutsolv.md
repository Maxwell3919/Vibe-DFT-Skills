# INPUT_PW — NAMELIST: &RISM — Variable: ecutsolv

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `ed6451075a52974cafc94926edbfdd9ded857c3518f771094bee7edffb9345f2`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ecutsolv
   
   Type:           REAL
   Default:        4 * "ecutwfc"
   Description:    Kinetic energy cutoff (Ry) for solvent's correlation functions.
                   If a solute is an isolated system or slab, you may allowed to
                   use default value. For a frameworked or porous solute (e.g. Zeolite, MOF),
                   it is desirable to apply a larger value. Solvents confined in a framework
                   often have a high frequency.
   +--------------------------------------------------------------------
   
```
