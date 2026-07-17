# INPUT_PWCOND — NAMELIST: &INPUTCOND — Variable: start_e

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PWCOND.txt
- Retrieved: 2026-07-17T11:49:48+00:00
- Official source SHA-256: `14fcee8af77391f494605bbcf53477d7c00e6d9e78555b3afd167462c8e53798`
- Extracted text SHA-256: `d1fc4b72a6e0e0faf9dc18c3654bccb5e9bcc6cf047bf0bafb1956fa878cbfba`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       start_e
   
   Type:           INTEGER
   Default:        1
   See:            last_e
   Description:    if start_e > 1, the scattering problem is solved only for those
                   energies with index between start_e and last_e in the energy list.
                   
                   NOTE: start_e <= last_e and start_e <= nenergy must be satisfied
   +--------------------------------------------------------------------
   
```
