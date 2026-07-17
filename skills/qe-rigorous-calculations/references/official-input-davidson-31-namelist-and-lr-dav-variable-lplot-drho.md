# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: lplot_drho

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `f233f2f034d44af58e5eeb1d566a56c2a35799bb0a605254e638155a3d92b703`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lplot_drho
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true. the turbo_davidson.x code will write
                   files for each eigenstate "drho-of-eign-$i" which are
                   needed to plot the response charge-density at each resonance.
                   This implies a calculation using the pp.x post-processing
                   program with the corresponding input file which must be
                   prepared. See example "H2O-PLOTRHO".
   +--------------------------------------------------------------------
   
```
