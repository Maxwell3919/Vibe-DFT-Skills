# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: last_step

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `a9c5c8efe098980eec8d7c4c9636d8511a41c3b21cd2fd1162f31c07ef585d27`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       last_step
   
   Type:           INTEGER
   Default:        0
   Description:    The program will end with step  istep <= "last_step".
                   If 0, it will stop at the end of the trajectory file
                   Note that this is not a sequential index but refers to the indexes reported in
                   the input trajectory file.
   +--------------------------------------------------------------------
   
```
