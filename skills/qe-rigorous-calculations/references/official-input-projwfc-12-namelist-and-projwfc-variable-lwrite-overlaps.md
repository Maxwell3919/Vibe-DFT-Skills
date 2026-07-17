# INPUT_PROJWFC — NAMELIST: &PROJWFC — Variable: lwrite_overlaps

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `03da174d7f3b846d16289a2a56b95501dae9bedb97e2572663efad56e78e3742`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       lwrite_overlaps
   
   Type:           LOGICAL
   Default:        .false.
   Description:    if .true., the overlap matrix of the atomic orbitals
                   prior to orthogonalization is written to "atomic_proj.xml".
                   Does not work together with parallel diagonalization:
                   for parallel runs, use "mpirun -np N projwfc.x -nd 1 ... "
   +--------------------------------------------------------------------
   
```
