# INPUT_EELS — NAMELIST: &LR_CONTROL — Variable: alpha_mix(i)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `924eb7c316f8c7c9d34f44b38ca9e76c476d1baae16c61b335153520c9027da0`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       alpha_mix(i)
   
   Type:           REAL
   Default:        alpha_mix(1)=0.7
   Description:    This variable is used only when "calculator" = 'sternheimer'.
                   Mixing parameter (for the i-th iteration) for updating
                   the response SCF potential using the modified Broyden
                   method: D.D. Johnson, PRB 38, 12807 (1988).
   +--------------------------------------------------------------------
   
```
