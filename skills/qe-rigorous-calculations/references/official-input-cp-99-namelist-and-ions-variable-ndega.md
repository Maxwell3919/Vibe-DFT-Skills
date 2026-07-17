# INPUT_CP — NAMELIST: &IONS — Variable: ndega

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `c438e450383e30d26ef0b21d22b61abe7a2c2570fa5e7cf42fde13f14f9c3383`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
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
