# INPUT_Davidson — NAMELIST: &LR_INPUT — Variable: restart

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `1e78271ec24bea6907b950e60946e499d983a748d454a70f2add5e4e9e99c4e9`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       restart
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true., turbo_davidson.x will attempt to restart
                   from a previous interrupted calculation if "max_seconds"
                   was specified.
                   Beware, if set to .false. turbo_davidson.x will OVERWRITE any
                   previous runs.
   +--------------------------------------------------------------------
   
```
