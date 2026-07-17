# INPUT_HP — NAMELIST: &INPUTHP — Variable: last_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `d0d387a718284cdb53e37144fa93a214f1f91c0fc72de9ff151998f7d0fc413a`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       last_q
   
   Type:           INTEGER
   Default:        number of q points
   See:            start_q, sum_pertq
   Description:    Computes only the q points from "start_q" to "last_q".
                   
                   IMPORTANT: "last_q" must be smaller or equal to
                   the total number of q points found.
   +--------------------------------------------------------------------
   
```
