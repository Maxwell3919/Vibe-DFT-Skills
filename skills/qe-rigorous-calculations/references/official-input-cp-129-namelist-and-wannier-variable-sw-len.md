# INPUT_CP — NAMELIST: &WANNIER — Variable: sw_len

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `a043efc9cf6fa707c80137beabfff3da6533c22ce68ae902946b59fec9cf900d`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       sw_len
   
   Type:           INTEGER
   Default:        1
   Description:    No. of iterations over which the field will be turned on
                   to its final value. Starting value is 0.0
                   If sw_len < 0, then it is set to 1.
                   If you want to just optimize structures on the presence of a
                   field, then you may set this to 1 and run a regular geometry
                   optimization.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      efx0, efy0, efz0
   
   Type:           REAL
   See:            0.D0
   Description:    Initial values of the field along x, y, and z directions
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      efx1, efy1, efz1
   
   Type:           REAL
   See:            0.D0
   Description:    Final values of the field along x, y, and z directions
   +--------------------------------------------------------------------
   
```
