# INPUT_PW — NAMELIST: &SYSTEM — Variable: dmft

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `b070451b721e2ebf5a51363e93451467245aff6799ce685c2a245b1500d25167`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dmft
   
   Type:           LOGICAL
   Default:        .FALSE.
   Status:         Requires compilation with hdf5 support
   Description:    If true, nscf calculation will exit in restart mode, scf calculation
                   will restart from there if DMFT updates are provided as hdf5 archive.
                   Scf calculation should be used only with "electron_maxstep" = 1.
                   "K_POINTS" have to be identical and given explicitly with "nosym".
   +--------------------------------------------------------------------
   
```
