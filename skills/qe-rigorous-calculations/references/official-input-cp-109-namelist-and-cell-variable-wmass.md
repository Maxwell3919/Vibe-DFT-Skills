# INPUT_CP — NAMELIST: &CELL — Variable: wmass

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `577ef068ce1eaf73a55a62cc81811ef67fdbc1da9a1e51cc97ef2e71c47aef05`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wmass
   
   Type:           REAL
   Default:        0.75*Tot_Mass/pi**2 for Parrinello-Rahman MD;
                   0.75*Tot_Mass/pi**2/Omega**(2/3) for Wentzcovitch MD
   Description:    Fictitious cell mass [amu] for variable-cell simulations
                   (both 'vc-md' and 'vc-relax')
   +--------------------------------------------------------------------
   
```
