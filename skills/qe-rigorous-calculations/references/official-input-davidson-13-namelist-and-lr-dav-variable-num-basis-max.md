# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: num_basis_max

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `4e61e27cd02c905652e25f2704c9dd1ea6f909e4af94664436ca7f2704a2c7ff`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       num_basis_max
   
   Type:           INTEGER
   Default:        20
   Description:    Maximum number of basis vectors allowed in the subspace.
                   When this number is reached, a discharging routine is called.
                   The memory requirement of the Davidson algorithm is mainly
                   determined by this variable (an estimation of the memory
                   is reported at the beginning of the run).
   +--------------------------------------------------------------------
   
```
