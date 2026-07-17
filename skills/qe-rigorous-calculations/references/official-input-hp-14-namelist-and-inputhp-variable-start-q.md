# INPUT_HP — NAMELIST: &INPUTHP — Variable: start_q

- Official source: https://www.quantum-espresso.org/Doc/INPUT_HP.txt
- Retrieved: 2026-07-17T11:49:15+00:00
- Official source SHA-256: `090eb912b6028fc7e2a44beac37167344ff2dde29b2485ca3010e01cbeede5e3`
- Extracted text SHA-256: `1455b94e65cbb3d417692e4be4f02dbf385a937238d8bae593e2d715f9f11466`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       start_q
   
   Type:           INTEGER
   Default:        1
   See:            last_q, sum_pertq
   Description:    Computes only the q points from "start_q" to "last_q".
                   
                   IMPORTANT: "start_q" must be smaller or equal to
                   the total number of q points found.
   +--------------------------------------------------------------------
   
```
