# INPUT_CP — NAMELIST: &SYSTEM — Variable: smearing

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `8e79463b891a6211929c95a10bd8ab6d4a83ae3a4f75aba1f6e727ba721d0dae`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       smearing
   
   Type:           CHARACTER
   Description:    a string describing the kind of occupations for electronic states
                   in the case of ensemble DFT (occupations == 'ensemble' );
                   possible values are: 'gaussian', 'fermi-dirac', 'hermite-delta',
                   'gaussian-splines', 'cold-smearing', 'marzari-vanderbilt', '0', '-1'.
                   Warning: only 'gaussian' is tested.
   +--------------------------------------------------------------------
   
```
