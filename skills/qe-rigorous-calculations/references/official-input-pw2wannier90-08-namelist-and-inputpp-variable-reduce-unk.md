# INPUT_pw2wannier90 — NAMELIST: &INPUTPP — Variable: reduce_unk

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2wannier90.txt
- Retrieved: 2026-07-17T11:50:02+00:00
- Official source SHA-256: `f551e64ec5d8230b6f2542a77af8133f42009c211a9284582530bace918c14c0`
- Extracted text SHA-256: `7ddf3551082cd895d72302260e1cde329861be98f00dc54a70ff7565a30a218c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       reduce_unk
   
   Type:           LOGICAL
   Description:    if .TRUE. reduce file-size (and resolution) of the real-space Bloch functions
                   by a factor of "reduce_unk_factor" along each direction.
                   Only relevant if "write_unk" = .true.
   Default:        .FALSE.
   +--------------------------------------------------------------------
   
```
