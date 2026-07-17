# INPUT_CP — NAMELIST: &IONS — Variable: nhptyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `4f9943a5ebd22f8f03717cef2efbd48ef0cabeb02c89caf8c7b25d0d0e4a2d2e`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nhptyp
   
   Type:           INTEGER
   Default:        0
   Description:    type of the "massive" Nose-Hoover chain thermostat
                   nhptyp=1 uses a NH chain per each atomic type
                   nhptyp=2 uses a NH chain per atom, this one is useful
                   for extremely rapid equipartitioning (equilibration is a
                   different beast)
                   nhptyp=3 together with nhgrp allows fine grained thermostat
                   control
                   NOTE: if using more than 1 thermostat per system there will
                   be a common thermostat added on top of them all, to disable
                   this common thermostat specify nhptyp=-X instead of nhptyp=X
   +--------------------------------------------------------------------
   
```
