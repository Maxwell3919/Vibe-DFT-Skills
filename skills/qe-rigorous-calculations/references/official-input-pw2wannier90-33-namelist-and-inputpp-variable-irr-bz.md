# INPUT_pw2wannier90 — NAMELIST: &INPUTPP — Variable: irr_bz

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2wannier90.txt
- Retrieved: 2026-07-17T11:50:02+00:00
- Official source SHA-256: `f551e64ec5d8230b6f2542a77af8133f42009c211a9284582530bace918c14c0`
- Extracted text SHA-256: `e9693f13c9df9e38acdb15fb9cae0d2d765c10e8e646c78fd179b8ea32df1188`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       irr_bz
   
   Type:           LOGICAL
   Description:    Set to .true. to use irreducible BZ for computing amn/mmn/eig
                   files. To differentiate from the standard full BZ case, the
                   files will use the extension names iamn/immn/ieig, respectively.
                   For more details, see the wannier90 user guide and examples.
   Default:        .FALSE.
   +--------------------------------------------------------------------
   
```
