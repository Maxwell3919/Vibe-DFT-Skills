# INPUT_PW — NAMELIST: &SYSTEM — Variable: ecutfock

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `00d9e56349cca6e85647f57ef5f993171687512642ad45b9365164c7b43bee56`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ecutfock
   
   Type:           REAL
   Default:        ecutrho
   Description:    Kinetic energy cutoff (Ry) for the exact exchange operator in
                   EXX type calculations. By default this is the same as "ecutrho"
                   but in some EXX calculations, a significant speed-up can be obtained
                   by reducing ecutfock, at the expense of some loss in accuracy.
                   Must be .gt. "ecutwfc". Not implemented for stress calculation
                   and for US-PP and PAW pseudopotentials.
                   Use with care, especially in metals where it may give raise
                   to instabilities.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nr1, nr2, nr3
   
   Type:           INTEGER
   Description:    Three-dimensional FFT mesh (hard grid) for charge
                   density (and scf potential). If not specified
                   the grid is calculated based on the cutoff for
                   charge density (see also "ecutrho")
                   Note: you must specify all three dimensions for this setting to
                   be used.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      nr1s, nr2s, nr3s
   
   Type:           INTEGER
   Description:    Three-dimensional mesh for wavefunction FFT and for the smooth
                   part of charge density ( smooth grid ).
                   Coincides with "nr1", "nr2", "nr3" if "ecutrho" = 4 * ecutwfc ( default )
                   Note: you must specify all three dimensions for this setting to
                   be used.
   +--------------------------------------------------------------------
   
```
