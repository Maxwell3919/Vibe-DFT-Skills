# INPUT_pw2wannier90 — NAMELIST: &INPUTPP — Variable: reduce_unk_factor

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2wannier90.txt
- Retrieved: 2026-07-17T11:50:02+00:00
- Official source SHA-256: `f551e64ec5d8230b6f2542a77af8133f42009c211a9284582530bace918c14c0`
- Extracted text SHA-256: `4022dda2ad2d580dbfdbf2b5bebed3426f33a0183465381ee14b2323f2e044a4`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       reduce_unk_factor
   
   Type:           INTEGER
   Description:    The reduction factor per direction for "reduce_unk". Default 2 means a reduction
                   of 2x2x2 = 8 of the total number of grid points.
                   Only relevant if "write_unk" = .true.
   Default:        1 if "reduce_unk" = .FALSE., 2 if "reduce_unk" = .TRUE.
   +--------------------------------------------------------------------
   
```
