# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: diag_basis

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `ab22bd775e65113de642aa2e3a91c477c227f6224ac45d5fccd289c97b61150f`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       diag_basis
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .false. the projections of Kohn-Sham states are
                                done on the orthogonalized atomic orbitals
                                in the global XYZ coordinate frame.
                   if .true. the projections of Kohn-Sham states are
                                done on the orthogonalized atomic orbitals
                                that are rotated to the basis in which the
                                atomic occupation matrix is diagonal
                                (i.e. local XYZ coordinate frame).
   +--------------------------------------------------------------------
   
```
