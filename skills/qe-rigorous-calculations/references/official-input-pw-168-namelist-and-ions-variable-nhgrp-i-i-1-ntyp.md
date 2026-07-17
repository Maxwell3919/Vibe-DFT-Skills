# INPUT_PW — NAMELIST: &IONS — Variable: nhgrp(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `674f461f9f82359bdfe6b6bcc955b23ad459f1338f2b4e014e60e506875bbfcd`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
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
