# INPUT_DOS — NAMELIST: &DOS — Variable: degauss

- Official source: https://www.quantum-espresso.org/Doc/INPUT_DOS.txt
- Retrieved: 2026-07-17T11:49:09+00:00
- Official source SHA-256: `d18fa270d3ca41b3bed586c40bb9cf5fb2b67962e741381a75bea23b6601eff3`
- Extracted text SHA-256: `68d85c936396feb5c2a655e7cbf0260cb2d35f589584bc4e6d05c2542ee2951d`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       degauss
   
   Type:           REAL
   Description:    gaussian broadening, Ry (not eV!)
                   (see below)
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      Emin, Emax
   
   Type:           REAL
   Default:        band extrema
   Description:    min, max energy (eV) for DOS plot. If unspecified, the
                   lower and/or upper band value, plus/minus 3 times the
                   value of the gaussian smearing if present, will be used.
   +--------------------------------------------------------------------
   
```
