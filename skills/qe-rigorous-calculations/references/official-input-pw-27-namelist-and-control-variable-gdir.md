# INPUT_PW — NAMELIST: &CONTROL — Variable: gdir

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d22e42b431e7950551416bb54b7657f31b3fbadb5a8f756d8ccff7a4d879ac86`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       gdir
   
   Type:           INTEGER
   Description:    For Berry phase calculation: direction of the k-point
                   strings in reciprocal space. Allowed values: 1, 2, 3
                   1=first, 2=second, 3=third reciprocal lattice vector
                   For calculations with finite electric fields
                   ("lelfield"==.true.) "gdir" is the direction of the field.
   +--------------------------------------------------------------------
   
```
