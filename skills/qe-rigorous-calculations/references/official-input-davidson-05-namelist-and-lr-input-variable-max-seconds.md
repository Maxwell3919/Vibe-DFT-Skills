# INPUT_Davidson — NAMELIST: &LR_INPUT — Variable: max_seconds

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `696786b20d0cc3f85210e34f5873b10c873ba4b0b7a17e7c8fdcba3cdfcc3be0`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       max_seconds
   
   Type:           REAL
   Default:        1.D+7, or 150 days, i.e. no time limit
   Description:    jobs stops after "max_seconds" CPU time. Use this option
                   in conjunction with option "restart" if you need to
                   split a job too long to complete into shorter jobs that
                   fit into your batch queues.
   +--------------------------------------------------------------------
   
```
