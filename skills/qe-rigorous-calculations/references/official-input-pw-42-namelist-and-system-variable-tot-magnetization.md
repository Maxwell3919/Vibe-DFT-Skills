# INPUT_PW — NAMELIST: &SYSTEM — Variable: tot_magnetization

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `726251375de3a0e7130e43386fd85def6db312af24c5ed0ebceaefbe0a8f0396`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tot_magnetization
   
   Type:           REAL
   Default:        -10000 [unspecified]
   Description:    Total majority spin charge - minority spin charge.
                   Used to impose a specific total electronic magnetization.
                   If unspecified then tot_magnetization variable is ignored and
                   the amount of electronic magnetization is determined during
                   the self-consistent cycle.
   +--------------------------------------------------------------------
   
```
