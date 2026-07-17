# INPUT_LD1 — NAMELIST: &INPUTP — Variable: lgipaw_reconstruction

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `1c5127fb7db03b0a23d1b30e8dbc1faee1703605d563ed837433c52c9b477219`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lgipaw_reconstruction
   
   Type:           LOGICAL
   Default:        .false.
   Description:    Set it to .true. to generate pseudo-potentials containing the
                   additional info required for reconstruction of all-electron
                   orbitals, used by GIPAW. You will typically need to specify
                   additional projectors beyond those used in the generation of
                   pseudo-potentials. You should also specify "file_recon".
                   
                   All projectors used in the reconstruction must be listed BOTH
                   in the test configuration after namelist &test AND in the
                   all-electron configuration (variable 'config', namelist &inputp,
                   Use negative occupancies for projectors on unbound states). The
                   core radii in the test configuration should be the same as in
                   the pseudo-potential generation section and will be used as the
                   radius of reconstruction. Projectors not used to generate the
                   pseudo-potential should have zero occupation number.
   +--------------------------------------------------------------------
   
```
