# INPUT_kcw — NAMELIST: &CONTROL — Variable: read_unitary_matrix

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `2934364f4bd18af5d499f20860088deb77b9b49ead9a767fe07d1a2de1e3e778`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       read_unitary_matrix
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If true read the Unitary matrix written by Wannier90.
                   Implicitely means a previous wannier90 calculation was
                   performed and a KCW calculation will be performed starting
                   from MLWF. Requires 'write_hr = .true.' in wannier90.
   +--------------------------------------------------------------------
   
```
