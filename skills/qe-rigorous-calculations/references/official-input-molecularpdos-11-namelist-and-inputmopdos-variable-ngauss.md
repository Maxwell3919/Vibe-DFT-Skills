# INPUT_molecularpdos — NAMELIST: &INPUTMOPDOS — Variable: ngauss

- Official source: https://www.quantum-espresso.org/Doc/INPUT_molecularpdos.txt
- Retrieved: 2026-07-17T11:49:57+00:00
- Official source SHA-256: `1e47fd2282c196dd8cfeb4de49502cedcb2fd40960784dcdc8b6955a6175cd8d`
- Extracted text SHA-256: `ae2ed5df930175d15731cab38366702c5125e728e0a19422f874d24d9227934f`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ngauss
   
   Type:           INTEGER
   Default:        0
   Description:    Type of gaussian broadening:
                       0 ... Simple Gaussian (default)
                       1 ... Methfessel-Paxton of order 1
                      -1 ... "cold smearing" (Marzari-Vanderbilt-DeVita-Payne)
                     -99 ... Fermi-Dirac function
   +--------------------------------------------------------------------
   
```
