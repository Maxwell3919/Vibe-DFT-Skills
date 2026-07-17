# INPUT_PW — NAMELIST: &SYSTEM — Variable: dftd3_version

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `27b9208ca8904bb7d858b8014a54a98ff8cbce9cad419f0b91bb1036cfaf874b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dftd3_version
   
   Type:           integer
   Default:        3
   Description:   
                   Version of Grimme implementation of Grimme-D3:
    
                   dftd3_version = 2 :
                        Original Grimme-D2 parametrization
    
                   dftd3_version = 3 :
                        Grimme-D3 (zero damping)
    
                   dftd3_version = 4 :
                        Grimme-D3 (BJ damping)
    
                   dftd3_version = 5 :
                        Grimme-D3M (zero damping)
    
                   dftd3_version = 6 :
                        Grimme-D3M (BJ damping)
    
                   NOTE: not all functionals are parametrized.
   +--------------------------------------------------------------------
   
```
