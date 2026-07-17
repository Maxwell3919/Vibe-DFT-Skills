# INPUT_CP — NAMELIST: &CONTROL — Variable: max_seconds

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `bd571fce530b4e4ec77d29f29f431b1ee0bd7388c8e4b335eb13db98c9ea1ccc`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       max_seconds
   
   Type:           REAL
   Default:        1.D+7, or 150 days, i.e. no time limit
   Description:    jobs stops after max_seconds CPU time. Used to prevent
                   a hard kill from the queuing system.
   +--------------------------------------------------------------------
   
```
