# INPUT_PW — NAMELIST: &IONS — Variable: tgdiis_step

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `45a7e1d7694e212174aecd000ca25841745133514716351bd0c7959caeb75121`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       tgdiis_step
      
      Type:           LOGICAL
      Default:        .true.
      Description:    When G-DIIS ("bfgs_ndim" > 1) is used for the structural relaxation this variable
                      selects whether to use to full gdiis step or the BFGS trus radius.
                      (bfgs only)
      +--------------------------------------------------------------------
      
```
