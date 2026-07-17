# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: ngauss

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `ae2ed5df930175d15731cab38366702c5125e728e0a19422f874d24d9227934f`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
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
