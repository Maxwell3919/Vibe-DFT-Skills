# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: poor_of_ram2

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `468c714f78004477f66dc8d63e8c3ace2fed2a83b60bc1098d0ae130ac9eee62`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       poor_of_ram2
   
   Type:           LOGICAL
   Default:        .false.
   Description:    Use this variable if you do not have enough RAM (NCPP and USPP),
                   i.e. set it to .true. When this variable is set to .false.,
                   you double the memory used for the calculation, but you
                   increase a speed of the calculation by storing D_ and C_
                   basis: the calculation will be speeded up a lot when
                   one is calculating many transitions at the same time.
   +--------------------------------------------------------------------
   
```
