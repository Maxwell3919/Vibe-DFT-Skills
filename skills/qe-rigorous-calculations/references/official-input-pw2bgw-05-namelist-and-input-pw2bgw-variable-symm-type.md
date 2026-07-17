# INPUT_pw2bgw — NAMELIST: &INPUT_PW2BGW — Variable: symm_type

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2bgw.txt
- Retrieved: 2026-07-17T11:49:58+00:00
- Official source SHA-256: `5f52150cf5d567429fbca7663ea1ecd3841683947b6ecfd410873e0a6d134e55`
- Extracted text SHA-256: `c780f8f7b2f2fe8545ea8ff53b9adbb2e0419189597296f3863a4789fe0b520c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       symm_type
   
   Type:           STRING
   Default:        'cubic'
   Description:   
                   Options are:
                        'cubic'
                        'hexagonal'
    
                   type of crystal system, 'cubic' for space groups 1 ... 142 and 195 ... 230
                   and 'hexagonal' for space groups 143 ... 194. Only used if ibrav = 0 in a
                   pw.x run. Written to BerkeleyGW WFN, RHO, VXC and VKB files but no longer
                   used (except in SAPO code in BerkeleyGW). You can use the default value for
                   all systems. Don't set to different values in different files for the same
                   system or you will get errors in BerkeleyGW.
   +--------------------------------------------------------------------
   
```
