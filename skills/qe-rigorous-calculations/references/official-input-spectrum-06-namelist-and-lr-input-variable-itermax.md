# INPUT_Spectrum — NAMELIST: &LR_INPUT — Variable: itermax

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Spectrum.txt
- Retrieved: 2026-07-17T11:49:51+00:00
- Official source SHA-256: `aa5de63566220ec9338215bdedcd16fa6ed031b02a440ef56150326a2aacb424`
- Extracted text SHA-256: `be8e7263f07d83d4eb737dd62447592eac9e4a959703aeb890e59c72b3e1e6bb`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       itermax
   
   Type:           INTEGER
   Default:        500
   Description:    The total number of Lanczos coefficients that will be
                   considered in the calculation of the polarizability/absorption
                   coefficient. If itermax > itermax0, the Lanczos coefficients
                   in between itermax0+1 and itermax will be extrapolated.
   +--------------------------------------------------------------------
   
```
