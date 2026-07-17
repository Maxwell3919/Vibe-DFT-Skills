# INPUT_PW — NAMELIST: &SYSTEM — Variable: nosym

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `9e13e1310f6547b8c351e523d3506fc9a16ca47c8b099015ed24fb2f3616c46d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nosym
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    if (.TRUE.) symmetry is not used. Consequences:
                   
                   - if a list of k points is provided in input, it is used
                     "as is": symmetry-inequivalent k-points are not generated,
                     and the charge density is not symmetrized;
                   
                   - if a uniform (Monkhorst-Pack) k-point grid is provided in
                     input, it is expanded to cover the entire Brillouin Zone,
                     irrespective of the crystal symmetry.
                     Time reversal symmetry is assumed so k and -k are considered
                     as equivalent unless "noinv"=.true. is specified.
                   
                   Do not use this option unless you know exactly what you want
                   and what you get. May be useful in the following cases:
                   - in low-symmetry large cells, if you cannot afford a k-point
                     grid with the correct symmetry
                   - in MD simulations
                   - in calculations for isolated atoms
   +--------------------------------------------------------------------
   
```
