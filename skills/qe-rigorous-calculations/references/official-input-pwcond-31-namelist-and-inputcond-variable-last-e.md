# INPUT_PWCOND — NAMELIST: &INPUTCOND — Variable: last_e

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `73431805e677f2fa1edbec16f0f43ba226493068ad5916b76498a66ddf5e3a12`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       last_e
   
   Type:           INTEGER
   Default:        nenergy
   See:            start_e
   Description:    index of the last energy to be computed. If last_e > nenergy,
                   then last_e will be automatically set to nenergy.
   +--------------------------------------------------------------------
   
```
