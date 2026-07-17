# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: trajdir

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `458b6109f7ddc9a394f578315c82855ca8578184b37e518f8a800cb94e07171d`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       trajdir
   
   Type:           CHARACTER
   Default:        ''
   Description:    Prefix of the cp.x trajectory. The program will try to open the files
                   "trajdir" .pos and "trajdir" .vel
                   The files, for n atoms, are formatted like this:
                   
                      NSTEP1 t_ps1
                      x(1) y(1) z(2)
                      .    .    .
                      .    .    .
                      .    .    .
                      x(n) y(n) z(n)
                      NSTEP2 t_ps2
                      x(1) y(1) z(2)
                      .    .    .
                      .    .    .
                      .    .    .
                      x(n) y(n) z(n)
                      ...
                   
                   the order of the atomic types must be the same of the one provided in the input file.
                   If the files are not found, only the positions and the velocities from the input file will be used.
                   Note that the units are specified by the input file. The units of the velocities are the same of
                   the positions with time in atomic units. If a cp.x trajectory is provided (see "vel_input_units" )
                   a factor 2 can be used for the velocities.
   +--------------------------------------------------------------------
   
```
