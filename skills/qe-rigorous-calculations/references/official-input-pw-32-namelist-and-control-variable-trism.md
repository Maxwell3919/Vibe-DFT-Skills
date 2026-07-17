# INPUT_PW — NAMELIST: &CONTROL — Variable: trism

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `73d46f3c3846b9afed69083d6d05c8e3e31f433f8a0088a5340b114befd15680`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       trism
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. perform a 3D-RISM-SCF calculation
                   [for details see H.Sato et al., JCP 112, 9463 (2000), doi:10.1063/1.481564].
                   The solvent's distributions are calculated by 3D-RISM,
                   though solute is treated as SCF. The charge density and
                   the atomic positions are optimized, simultaneously with
                   the solvents. To perform the calculation, you must set
                   a namelist "RISM" and a card "SOLVENTS".
                   
                   If "assume_isolated" = 'esm' and "esm_bc" = 'bc1',
                   Laue-RISM is calculated instead of 3D-RISM
                   and coupled with ESM method (i.e. ESM-RISM).
                   [for details see S.Nishihara and M.Otani, PRB 96, 115429 (2017)].
                   
                   The default of "mixing_beta" is 0.2
                   for both 3D-RISM and Laue-RISM.
                   
                   For structural relaxation with BFGS,
                   "ignore_wolfe" is always .TRUE. .
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
