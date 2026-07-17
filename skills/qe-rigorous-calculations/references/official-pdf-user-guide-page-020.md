# user_guide.pdf — page 20

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `657d041c23e715c4a9d65740de99605a7100541955a79efbd7fcf2e990d0b9de`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2.8.1     Test-suite
Automated tests give a ”pass/fail” answer. All tests run quickly (less than a minute each at
most), but they are not meant to be realistic, just to test a specific case. Many features are
tested but only for the following codes: pw.x, cp.x, ph.x, epw.x, hp.x. Instructions for the
impatient:
    cd test-suite
    make [NPROCS=X] run-tests
where the square brackets mean that what is inside is optional, X is the number of processors
(for a parallel build: do not set X to more than 1 for a serial build!).
    Instructions for all others: go to the test-suite/ directory, read the README file, or at
least, type make. You may need to edit the run-XX.sh shells, defining variables PARA PREFIX
and PARA POSTFIX (see below for their meaning).

2.8.2     Examples
There are many examples and reference data for almost every piece of Quantum ESPRESSO,
but you have to manually inspect the results.
   In order to use examples, you should edit file environment variables, setting the following
variables as needed.
        BIN DIR: directory where executables reside
        PSEUDO DIR: directory where pseudopotential files reside
        TMP DIR: directory to be used as temporary storage area
The default values of BIN DIR and PSEUDO DIR should be fine, unless you have installed
things in nonstandard places. TMP DIR must be a directory where you have read and write
access to, with enough available space to host the temporary files produced by the example
runs, and possibly offering high I/O performance (i.e., don’t use an NFS-mounted directory).
NOTA BENE: do not use a directory containing other data: the examples will clean it!
    If you have compiled the parallel version of Quantum ESPRESSO (this is the default
if parallel libraries are detected), you will usually have to specify a launcher program (such
as mpirun or mpiexec) and the number of processors: see Sec.3 for details. In order to do
that, edit again the environment variables file and set the PARA PREFIX and PARA POSTFIX
variables as needed. Parallel executables will be run by a command like this:
         $PARA_PREFIX pw.x $PARA_POSTFIX -i file.in > file.out
For example, if the command line is like this (as for an IBM SP):
         mpirun -np 4 pw.x -i file.in > file.out
you should set PARA PREFIX="mpirun -np 4", PARA POSTFIX="". Furthermore, if your ma-
chine does not support interactive use, you must run the commands specified above through
the batch queuing system installed on that machine. Ask your system administrator for instruc-
tions. For execution using OpenMP on N threads, use PARA PREFIX="env OMP NUM THREADS=N
... ".
    To run an example, go to the corresponding directory (e.g. PW/examples/example01) and
execute:

                                             20
```
