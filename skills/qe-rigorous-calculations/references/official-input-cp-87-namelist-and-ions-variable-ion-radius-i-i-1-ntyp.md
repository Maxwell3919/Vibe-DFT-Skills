# INPUT_CP — NAMELIST: &IONS — Variable: ion_radius(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `b453ad9099cf2fdba3d5fd2c4b14b23c075f1cadbd405bb5020062ee129e8258`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_radius(i), i=1,ntyp
   
   Type:           REAL
   Default:        0.5 a.u. for all species
   Description:    ion_radius(i): pseudo-atomic radius of the i-th atomic species
                   used in Ewald summation. Typical values: between 0.5 and 2.
                   Results should NOT depend upon such parameters if their values
                   are properly chosen. See also "iesr".
   +--------------------------------------------------------------------
   
```
