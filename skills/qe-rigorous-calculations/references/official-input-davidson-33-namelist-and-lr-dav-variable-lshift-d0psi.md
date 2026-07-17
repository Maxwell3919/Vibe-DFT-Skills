# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: lshift_d0psi

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `8c9ed0cbbfe55b751434080f1b300a62861946d804f82599f1d1f3d012917e0e`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lshift_d0psi
   
   Type:           LOGICAL
   Default:        .true.
   Description:    This variable is used only when "d0psi_rs" = .true.
                   a) If a molecule is placed in the corner of the
                   supercell, there is a discontinuity problem for the
                   position operator r, which is not periodic. By setting
                   "lshift_d0psi" = .true. the discontinuity problem is
                   solved by shifting the position operator r such that
                   it is continuous and well defined.
                   b) If a molecule is placed in the center of the supercell,
                   there is no discontinuity problem for the position operator r,
                   and thus you can set "lshift_d0psi" = .false. But if you still
                   set it to .true., this will not harm, because the position
                   operator will basically remain as it is, since it is always
                   centered wrt the center of the molecule.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:26:49 CEST 2025
```
