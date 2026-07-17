# INPUT_CP — NAMELIST: &IONS — Variable: ion_positions

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `8bcb48aa4bc1c8a4033c8415b7ee3489e020dff3af842c62b346e6908859284e`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_positions
   
   Type:           CHARACTER
   Default:        'default'
   Description:    'default '  : if restarting, use atomic positions read from the
                                 restart file; in all other cases, use atomic
                                 positions from standard input.
                   
                   'from_input' : restart the simulation with atomic positions read
                                 from standard input, even if restarting.
   +--------------------------------------------------------------------
   
```
