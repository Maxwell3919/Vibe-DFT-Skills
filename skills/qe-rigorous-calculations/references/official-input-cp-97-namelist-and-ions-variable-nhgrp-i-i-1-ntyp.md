# INPUT_CP — NAMELIST: &IONS — Variable: nhgrp(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `01f6ceb89465af77f34d3cf9dec3e22a130f98ecbc4cbd47a87a86ed2ea7bbaf`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nhgrp(i), i=1,ntyp
   
   Type:           INTEGER
   Default:        0
   Description:    specifies which thermostat group to use for given atomic type
                   when >0 assigns all the atoms in this type to thermostat
                   labeled nhgrp(i), when =0 each atom in the type gets its own
                   thermostat. Finally, when <0, then this atomic type will have
                   temperature "not controlled". Example: HCOOLi, with types H (1), C(2), O(3), Li(4);
                   setting nhgrp={2 2 0 -1} will add a common thermostat for both H & C,
                   one thermostat per each O (2 in total), and a non-updated thermostat
                   for Li which will effectively make temperature for Li "not controlled"
   +--------------------------------------------------------------------
   
```
