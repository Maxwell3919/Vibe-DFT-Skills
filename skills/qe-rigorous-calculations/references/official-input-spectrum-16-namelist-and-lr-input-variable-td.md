# INPUT_Spectrum — NAMELIST: &LR_INPUT — Variable: td

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Spectrum.txt
- Retrieved: 2026-07-17T11:49:51+00:00
- Official source SHA-256: `aa5de63566220ec9338215bdedcd16fa6ed031b02a440ef56150326a2aacb424`
- Extracted text SHA-256: `187e6b1c7542147fd41f9bd398318dfea7cbdfea22e23ffaf53095a709f129da`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       td
   
   Type:           CHARACTER
   Default:        'lanczos'
   Description:    When set to 'lanczos', a calculation of the spectrum is
                   performed using the Lanczos coefficients.
                   When set to 'davidson' or 'david', a calculation of the
                   spectrum is performed using the eigenvalues computed
                   using the Davidson algorithm. See the variable 'eign_file'.
   +--------------------------------------------------------------------
   
```
