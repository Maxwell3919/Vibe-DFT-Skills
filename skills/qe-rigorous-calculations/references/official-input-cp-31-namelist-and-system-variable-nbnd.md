# INPUT_CP — NAMELIST: &SYSTEM — Variable: nbnd

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `32d3bd55c08ccc05b442d6bb0fe684e740be44a3872eb1eddf53e0e46f61c700`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nbnd
   
   Type:           INTEGER
   Default:        for an insulator, nbnd = number of valence bands
                   (nbnd = # of electrons /2);
                   for a metal, 20% more (minimum 4 more)
   Description:    number of electronic states (bands) to be calculated.
                   Note that in spin-polarized calculations the number of
                   k-point, not the number of bands per k-point, is doubled
   +--------------------------------------------------------------------
   
```
