# INPUT_PWCOND — NAMELIST: &INPUTCOND — Variable: recover

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `f29ef12d5302c7e7ebaf94745c92c52aabbbf403d5dd2194c987b87fdfeab30b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       recover
   
   Type:           LOGICAL
   Default:        .FALSE.
   See:            tran_prefix
   Description:    restarts a previously interrupted transmission calculation (only if
                   tran_prefix was specified). It can also be used to gather partial
                   results from a calculation that was split by using start_e,last_e
                   and/or start_k,last_k (see corresponding keywords).
   +--------------------------------------------------------------------
   
```
