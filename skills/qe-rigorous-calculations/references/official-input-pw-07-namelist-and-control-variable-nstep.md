# INPUT_PW — NAMELIST: &CONTROL — Variable: nstep

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `3cf73c7c5e209d3b6603ffd43d0e538651b7dd53a306614348913d757d724583`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nstep
   
   Type:           INTEGER
   Description:    number of molecular-dynamics or structural optimization steps
                   performed in this run. If set to 0, the code performs a quick
                   "dry run", stopping just after initialization. This is useful
                   to check for input correctness and to have the summary printed.
                   NOTE: in MD calculations, the code will perform "nstep" steps
                   even if restarting from a previously interrupted calculation.
   Default:        1  if "calculation" == 'scf', 'nscf', 'bands';
                   50 for the other cases
   +--------------------------------------------------------------------
   
```
