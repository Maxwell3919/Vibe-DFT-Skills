# INPUT_PW — NAMELIST: &IONS — Variable: nhptyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `ce3ea09157fee2da274f7187628268928f2e8814ba5f68a27c4347a9edfa7897`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       nhptyp
      
      Type:           INTEGER
      Default:        0
      Description:    type of the "massive" Nose-Hoover chain thermostat:
                       * nhptyp = 0 usese one NH chain for all atoms.
                       * nhtyp=1 uses a  NH chain per each atomic type
                       * nhptyp=2 use a NH chaing per atom, this one is usefulf
                         for extremely rapid equipartioning.
                       * nhptyp =3 together with "nhgrp" allows fine grained thermostat
                         control
      +--------------------------------------------------------------------
      
```
