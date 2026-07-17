# INPUT_PW — NAMELIST: &CELL — Variable: wmass

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `577ef068ce1eaf73a55a62cc81811ef67fdbc1da9a1e51cc97ef2e71c47aef05`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
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
