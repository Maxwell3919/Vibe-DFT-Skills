# INPUT_CP — NAMELIST: &SYSTEM — Variable: ecutrho

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `cd04fdc81e61bfacd57d6e49d6c2e95ad6cf7057f5f38a07dfa142b4696daab3`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ecutrho
   
   Type:           REAL
   Default:        4 * ecutwfc
   Description:    kinetic energy cutoff (Ry) for charge density and potential
                   For norm-conserving pseudopotential you should stick to the
                   default value, you can reduce it by a little but it will
                   introduce noise especially on forces and stress.
                   If there are ultrasoft PP, a larger value than the default is
                   often desirable (ecutrho = 8 to 12 times ecutwfc, typically).
                   PAW datasets can often be used at 4*ecutwfc, but it depends
                   on the shape of augmentation charge: testing is mandatory.
                   The use of gradient-corrected functional, especially in cells
                   with vacuum, or for pseudopotential without non-linear core
                   correction, usually requires an higher values of ecutrho
                   to be accurately converged.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nr1, nr2, nr3
   
   Type:           INTEGER
   See:            ecutrho
   Description:    three-dimensional FFT mesh (hard grid) for charge
                   density (and scf potential). If not specified
                   the grid is calculated based on the cutoff for
                   charge density.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nr1s, nr2s, nr3s
   
   Type:           INTEGER
   Description:    three-dimensional mesh for wavefunction FFT and for the smooth
                   part of charge density ( smooth grid ).
                   Coincides with nr1, nr2, nr3 if ecutrho = 4 * ecutwfc ( default )
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nr1b, nr2b, nr3b
   
   Type:           INTEGER
   Description:    dimensions of the "box" grid for Ultrasoft pseudopotentials
                   must be specified if Ultrasoft PP are present
   +--------------------------------------------------------------------
   
```
