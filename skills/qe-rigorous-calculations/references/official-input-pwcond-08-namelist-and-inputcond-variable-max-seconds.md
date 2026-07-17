# INPUT_PWCOND — NAMELIST: &INPUTCOND — Variable: max_seconds

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `e24d885c16f860f3f27d235a0a9cd930e3ea94c4906f96a30a43f45c6050373d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       max_seconds
   
   Type:           REAL
   Default:        1.D+7, or 150 days, i.e. no time limit
   See:            tran_prefix
   Description:    jobs stops after max_seconds elapsed time (wallclock time).
                   It can be enabled only if tran_prefix is specified.
   +--------------------------------------------------------------------
   
```
