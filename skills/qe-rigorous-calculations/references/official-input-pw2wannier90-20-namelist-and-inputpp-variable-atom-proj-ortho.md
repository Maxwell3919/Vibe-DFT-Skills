# INPUT_pw2wannier90 — NAMELIST: &INPUTPP — Variable: atom_proj_ortho

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2wannier90.txt
- Retrieved: 2026-07-17T11:50:02+00:00
- Official source SHA-256: `f551e64ec5d8230b6f2542a77af8133f42009c211a9284582530bace918c14c0`
- Extracted text SHA-256: `0322623530ac9dd5e560e7741eb3e051c6f8ba7b17dc3bb590b7ed39edf624ff`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       atom_proj_ortho
   
   Type:           LOGICAL
   Description:    Set to .true. to orthonormalize the pseudo-atomic wavefunctions
                   before computing the inner product between Bloch states and
                   the pseudo-atomic wavefunctions.
                   It is recommended to keep this to .true., set it to .false. only
                   if you know what you are doing.
                   Only relevant if "atom_proj" = .true.
   Default:        .TRUE.
   +--------------------------------------------------------------------
   
```
