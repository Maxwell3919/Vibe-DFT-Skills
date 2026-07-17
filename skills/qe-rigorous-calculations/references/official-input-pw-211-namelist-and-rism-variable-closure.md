# INPUT_PW — NAMELIST: &RISM — Variable: closure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `01304a986721598a8f6cb25e85d063c4a7e368384c62b24ae556c20c44685ce8`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       closure
   
   Type:           CHARACTER
   Default:        'kh'
   Description:   
                   Specify the type of closure equation:
    
                   'kh' :
                        The Kovalenko and Hirata's model.
                        [A.Kovalenko, F.Hirata, JCP 110, 10095 (1999), doi:10.1063/1.478883]
    
                   'hnc' :
                        The HyperNetted-Chain model, which is
                        suitable only for solvents without charge.
                        [J.P.Hansen et al., Theory of simple liquids. Academic Press, London, 1990]
   +--------------------------------------------------------------------
   
```
