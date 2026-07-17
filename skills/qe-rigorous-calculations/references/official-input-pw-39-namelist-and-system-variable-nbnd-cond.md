# INPUT_PW — NAMELIST: &SYSTEM — Variable: nbnd_cond

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `4956a90f012f43c9e43d363ed8cf55267bb5d7ba1b46adc5606a646b9ce0a439`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nbnd_cond
   
   Type:           INTEGER
   Default:        nbnd_cond = "nbnd" - # of electrons / 2 in the collinear case;
                                        nbnd_cond = "nbnd" - # of electrons in the noncollinear case.
   Description:    Number of electronic states in the conduction manifold
                   for a two chemical-potential calculation ("twochem"=.true.).
   +--------------------------------------------------------------------
   
```
