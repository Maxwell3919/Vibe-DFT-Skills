# INPUT_pw2wannier90 — NAMELIST: &INPUTPP — Variable: write_sHu

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2wannier90.txt
- Retrieved: 2026-07-17T11:50:02+00:00
- Official source SHA-256: `f551e64ec5d8230b6f2542a77af8133f42009c211a9284582530bace918c14c0`
- Extracted text SHA-256: `b67d785084b11bc6cda9d781a345d6c431dfe6a5fe5c30d7d3f6aa156791e5c7`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       write_sHu
   
   Type:           LOGICAL
   Description:    Set to .true. to write out the matrix elements of
                   < unk | s H | umk+b >, which is used in the Ryoo's method
                   to compute spin Hall conductivity. For more details, see the
                   wannier90 user guide and examples.
   Default:        .FALSE.
   +--------------------------------------------------------------------
   
```
