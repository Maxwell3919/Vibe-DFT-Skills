# INPUT_LD1 — NAMELIST: &INPUT — Variable: config

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `f085af71afd683271c022085a12fb933e0ec9998c84dd179cbca975779b7b1af`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       config
   
   Type:           CHARACTER
   Default:        ' '
   Description:    A string with the electronic configuration.
                   
                   Example:
                     '[Ar] 3d10 4s2 4p2.5'
                   
                   * If "lsd"=1, spin-up and spin-down state may appear twice
                     with the respective occupancy: 3p4 3p2 = 4 up,
                     2 down. Otherwise, the Hund's rule is assumed.
                   
                   * If "rel"=2, states with jj=l-1/2 are filled first.
                     If a state appears twice, the first one has jj=l-1/2,
                     the second one jj=l+1/2 (except S states)
                     (Use rel_dist if you want to average the electrons
                     over all available states.)
                   
                   * If config='default' the code uses "zed" to set the ground
                     state electronic configuration for the atom.
                   
                   Negative occupancies are used to flag unbound states;
                   they are not actually used.
   +--------------------------------------------------------------------
   
```
