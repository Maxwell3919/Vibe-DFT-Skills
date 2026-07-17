# INPUT_CP — NAMELIST: &WANNIER — Variable: nwf

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `e7e93c60aeeb3bae1ac0c3182208fdcb57b74d2070f465b1710f53cdde067cf4`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       nwf
   
   Type:           INTEGER
   Default:        0
   Description:    This option is used with calwf 1 and calwf 5. with calwf=1,
                   it tells the code how many Orbital densities are to be
                   output. With calwf=5, set this to 1(i.e calwf=5 only writes
                   one state during one run. so if you want 10 states, you have
                   to run the code 10 times). With calwf=1, you can print many
                   orbital densities in a single run.
                   See also the PLOT_WANNIER card for specifying the states to
                   be printed.
   +--------------------------------------------------------------------
   
```
