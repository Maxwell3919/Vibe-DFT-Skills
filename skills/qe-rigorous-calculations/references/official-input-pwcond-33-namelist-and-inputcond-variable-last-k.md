# INPUT_PWCOND — NAMELIST: &INPUTCOND — Variable: last_k

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `2959d87411c680d4e423a3a2ae1ddcab586900beff35f925c0a825319cbd96ae`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       last_k
   
   Type:           INTEGER
   Default:        nenergy
   See:            start_k
   Description:    index of the last k-point to be computed. If last_k is bigger than the
                   actual number of points in the list, then it will be set to that number.
   +--------------------------------------------------------------------
   
```
