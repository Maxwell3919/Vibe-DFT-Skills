# INPUT_pw2wannier90 — NAMELIST: &INPUTPP — Variable: atom_proj_exclude(i), i=1,n_exclude_proj

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2wannier90.txt
- Retrieved: 2026-07-17T11:50:02+00:00
- Official source SHA-256: `f551e64ec5d8230b6f2542a77af8133f42009c211a9284582530bace918c14c0`
- Extracted text SHA-256: `02a65a1b57172dbe2b3956dc0025aba2ecd59f5303ef03d75ec7f459a29dd07c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       atom_proj_exclude(i), i=1,n_exclude_proj
   
   Type:           INTEGER
   Description:    Set to the index of the pseudo-atomic wavefunctions to be excluded
                   from the initial projection. This is useful for excluding the
                   semicore states from the initial projection.
                   Only relevant if "atom_proj" = .true.
   Default:        empty
   +--------------------------------------------------------------------
   
```
