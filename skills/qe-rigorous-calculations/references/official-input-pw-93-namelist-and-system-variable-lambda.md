# INPUT_PW — NAMELIST: &SYSTEM — Variable: lambda

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `968528d8a19682f407c33d2d82d2e9bc4b722be5ba0b09d780212eb35c98f871`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lambda
   
   Type:           REAL
   See:            constrained_magnetization
   Default:        1.d0
   Description:    parameter used for constrained_magnetization calculations
                   N.B.: if the scf calculation does not converge, try to reduce lambda
                         to obtain convergence, then restart the run with a larger lambda
   +--------------------------------------------------------------------
   
```
