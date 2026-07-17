# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: n_workers

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `813210175a20388d4af101672738c0d7239cf088be69362ee781b032c7a9785d`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       n_workers
   
   Type:           INTEGER
   Default:        0
   Description:    The calculation over all the trajectory is splitted in "n_workers" chunks. Then to run the code over all
                   the trajectory you must run "n_workers" input files each one with a different "worker_id",
                   from 0 to "n_workers" - 1 . Those inputs can run at the same time in the same folder. The "worker_id"
                   will be appended to the outdir folder and to the "file_output" input variables, so you can safely run all
                   the inputs in the same directory at the same time.
   +--------------------------------------------------------------------
   
```
