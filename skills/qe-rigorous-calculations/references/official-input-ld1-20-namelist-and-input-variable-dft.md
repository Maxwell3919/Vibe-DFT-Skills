# INPUT_LD1 — NAMELIST: &INPUT — Variable: dft

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `6d18ae7696065db6f11b89c733dbeb91033c6030ec1100ff4acf44427198413b`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       dft
   
   Type:           CHARACTER
   Description:    Exchange-correlation functional.
                   
                   Examples:
                   'PZ'    Perdew and Zunger formula for LDA
                   'PW91'  Perdew and Wang GGA
                   'BP'    Becke and Perdew GGA
                   'PBE'   Perdew, Becke and Ernzerhof GGA
                   'BLYP'  ...
                   
                   For the complete list, see module "functionals" in ../Modules/
                   The default is 'PZ' for all-electron calculations,
                   it is read from the PP file in a PP calculation.
   +--------------------------------------------------------------------
   
```
