# INPUT_PW — NAMELIST: &CONTROL — Variable: max_seconds

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `ab683c8247bcf7a12c93e822b96260c7a8ca443818f6293daf02fee011980b1a`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       max_seconds
   
   Type:           REAL
   Default:        1.D+7, or 150 days, i.e. no time limit
   Description:    Jobs stops after "max_seconds" CPU time. Use this option
                   in conjunction with option "restart_mode" if you need to
                   split a job too long to complete into shorter jobs that
                   fit into your batch queues.
   +--------------------------------------------------------------------
   
```
