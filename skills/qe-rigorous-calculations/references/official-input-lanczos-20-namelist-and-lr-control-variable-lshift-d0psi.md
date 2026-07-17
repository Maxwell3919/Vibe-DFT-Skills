# INPUT_Lanczos — NAMELIST: &LR_CONTROL — Variable: lshift_d0psi

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Lanczos.txt
- Retrieved: 2026-07-17T11:49:18+00:00
- Official source SHA-256: `58c02f4cb1fdefbef4203bbe55d16af2a768acd7cfb5462fc62bd1dfd07cb530`
- Extracted text SHA-256: `25bb02c61da3f252b6761c0bcc5ee3abdd3cfafe7b7626b1b6eced236e73df6a`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
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
                   lshift_d0psi=.true. the discontinuity problem is
                   solved by shifting the position operator r such that
                   it is continuous and well defined.
                   b) If a molecule is placed in the center of the supercell,
                   there is no discontinuity problem for the position operator r,
                   and thus you can set lshift_d0psi=.false. But if you still
                   set it to .true., this will not harm, because the position
                   operator will basically remain as it is, since it is always
                   centered wrt the center of the molecule.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
