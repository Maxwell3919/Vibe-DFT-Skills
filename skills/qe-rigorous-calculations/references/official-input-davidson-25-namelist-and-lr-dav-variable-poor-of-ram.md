# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: poor_of_ram

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `2ef6c15a948258febd6485b84fe8b7bbf3d9d8d7bb73f64c4c57df9d1d31ee66`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       poor_of_ram
   
   Type:           LOGICAL
   Default:        .false.
   Description:    Use this variable if you do not have enough RAM (only USPP),
                   i.e. set it to .true. When this variable is set to .false.,
                   you double the memory used for the USPP calculation, but you
                   increase a speed of the calculation by getting rid of
                   applying many times of s_psi and cal_bec in the
                   calculation, which takes a lot of time (sometimes more than
                   a half of the whole calculation) when the size of the
                   subspace is more than 100.
   +--------------------------------------------------------------------
   
```
