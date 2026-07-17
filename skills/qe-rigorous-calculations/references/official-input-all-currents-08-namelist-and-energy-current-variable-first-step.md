# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: first_step

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `9e6a9a6d1ade070622db5737d56704322b60551192d4ff0d60047673369173ba`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       first_step
   
   Type:           INTEGER
   Default:        0
   Description:    The program will start with step  istep >= "first_step".
                   If greater than zero the input file's positions and velocities will be ignored.
                   Note that this is not a sequential index but refers to the indexes reported in
                   the input trajectory file. The index of 0 is assigned to the snapshot described
                   in the input namelist file.
   +--------------------------------------------------------------------
   
```
