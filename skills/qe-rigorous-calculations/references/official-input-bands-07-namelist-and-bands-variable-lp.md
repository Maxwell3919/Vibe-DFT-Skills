# INPUT_BANDS — NAMELIST: &BANDS — Variable: lp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BANDS.txt
- Retrieved: 2026-07-17T11:48:54+00:00
- Official source SHA-256: `b8b1193c4f2723310151d7825240f9b20fe2212d1e0f509cce89988a93f7a14a`
- Extracted text SHA-256: `207c1b7dac92cd740c7bb2aebbc00753b92f562a806ab11bcdcaacd62d846106`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lp
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true. matrix elements of the momentum operator p between
                   conduction and valence bands are computed and written to file
                   specified in "filp".
                   The matrix elements include the contribution from the nonlocal
                   potential, i*m*[V_nl, x]. In other words, the calculated matrix elements
                   are those of the velocity operator i*m*[H, x] times mass, not those of
                   the true momentum operator.
   +--------------------------------------------------------------------
   
```
