# INPUT_PW — NAMELIST: &IONS — Variable: ndega

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `5b7093396d947defb8e79c5b1c672e80fadff37ea7ed4becb6b7e35a0093a8b2`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       ndega
      
      Type:           INTEGER
      Default:        0
      Description:    number of degrees of freedom used for temperature calculation
                      ndega <= 0 sets the number of degrees of freedom to
                      [3*nat-abs(ndega)], ndega > 0 is used as the target number
      +--------------------------------------------------------------------
      
```
