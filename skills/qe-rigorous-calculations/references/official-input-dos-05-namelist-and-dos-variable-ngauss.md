# INPUT_DOS — NAMELIST: &DOS — Variable: ngauss

- Official source: https://www.quantum-espresso.org/Doc/INPUT_DOS.txt
- Retrieved: 2026-07-17T11:49:09+00:00
- Official source SHA-256: `d18fa270d3ca41b3bed586c40bb9cf5fb2b67962e741381a75bea23b6601eff3`
- Extracted text SHA-256: `77ad72105272cee4d0846f6d0f12849a5e1bf26344e772554bc0a027192c5608`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ngauss
   
   Type:           INTEGER
   Default:        0
   Status:         optional
   Description:    Type of gaussian broadening:
                   
                       =  0  Simple Gaussian (default)
                   
                       =  1  Methfessel-Paxton of order 1
                   
                       = -1  "cold smearing" (Marzari-Vanderbilt-DeVita-Payne)
                   
                       =-99  Fermi-Dirac function
   +--------------------------------------------------------------------
   
```
