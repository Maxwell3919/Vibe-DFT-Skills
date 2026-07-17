# user_guide.pdf — page 30

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `cd11797344cacfc4ffb3a169369b63313fbd2ca4a33e314390431bab821965ed`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Of course the input file must be accessible by the processor that must read it (only one processor
reads the input file and subsequently broadcasts its contents to all other processors).
   Apparently the LSF implementation of MPI libraries manages to ignore or to confuse even
the -i/in/inp/input mechanism that is present in all Quantum ESPRESSO codes. In this
case, use the -i option of mpirun.lsf to provide an input file.

Trouble with MPI-OpenMP parallelization It is often advantageous to compile for both
MPI and OpenMP parallelization, taking advantage of both. If however you get really bad
performances, you may have run into a conflict between the two parallelizations, leading to
more than one thread trying to access the same core.
    Quantum ESPRESSO cannot control where MPI processes and OpenMP thread execute:
this is something that the operating system should know about. All you can control is the
number of MPI processes (with mpirun) and of OpenMP threads per MPI process (with the
environment variable OMP NUM THREADS=N). If you are out of luck and of better ideas,
just set OMP NUM THREADS=1,




                                               30
```
