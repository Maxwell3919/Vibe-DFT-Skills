# INPUT_CP — NAMELIST: &CONTROL — Variable: memory

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `529affcb45b3bb819d582b629e8261daf0e804bc11183fcce5eccf0f0c6db67d`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       memory
   
   Type:           CHARACTER
   Default:        'default'
   Description:    'small': NO LONGER IMPLEMENTED SINCE v.6.3
                            memory-saving tricks are implemented. Currently:
                            - the G-vectors are sorted only locally, not globally
                            - they are not collected and written to file
                            For large systems, the memory and time gain is sizable
                            but the resulting data files are not portable - use it
                            only if you do not need to re-read the data file
   +--------------------------------------------------------------------
   
```
