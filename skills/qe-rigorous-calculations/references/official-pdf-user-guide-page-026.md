# user_guide.pdf — page 26

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `388f1a0cdcbd7849aeda2274020cbe0d23a98312a397d3d4a6e51553fea86a34`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3     Parallelism
3.1     Understanding Parallelism
Two different parallelization paradigms are currently implemented in Quantum ESPRESSO:

    1. Message-Passing (MPI). A copy of the executable runs on each CPU; each copy lives in a
       different world, with its own private set of data, and communicates with other executables
       only via calls to MPI libraries. MPI parallelization requires compilation for parallel
       execution, linking with MPI libraries, execution using a launcher program (depending
       upon the specific machine). The number of CPUs used is specified at run-time either as
       an option to the launcher or by the batch queue system.

    2. OpenMP. A single executable spawn subprocesses (threads) that perform in parallel spe-
       cific tasks. OpenMP can be implemented via compiler directives (explicit OpenMP) or
       via multithreading libraries (library OpenMP). Explicit OpenMP require compilation for
       OpenMP execution; library OpenMP requires only linking to a multithreading version
       of the mathematical libraries. The number of threads is specified at run-time in the
       environment variable OMP NUM THREADS.

    MPI is the well-established, general-purpose parallelization. In Quantum ESPRESSO
several parallelization levels, specified at run-time via command-line options to the executable,
are implemented with MPI. This is your first choice for execution on a parallel machine.
    The support for explicit OpenMP is steadily improving. Explicit OpenMP can be used
together with MPI and also together with library OpenMP. Beware conflicts between the various
kinds of parallelization! If you don’t know how to run MPI processes and OpenMP threads in
a controlled manner, forget about mixed OpenMP-MPI parallelization.

3.2     Running on parallel machines
Parallel execution is strongly system- and installation-dependent. Typically one has to specify:

    1. a launcher program such as mpirun or mpiexec, with the appropriate options (if any);

    2. the number of processors, typically as an option to the launcher program;

    3. the program to be executed, with the proper path if needed;

    4. other Quantum ESPRESSO-specific parallelization options, to be read and interpreted
       by the running code.

Items 1) and 2) are machine- and installation-dependent, and may be different for interactive
and batch execution. Note that large parallel machines are often configured so as to disallow
interactive execution: if in doubt, ask your system administrator. Item 3) also depend on your
specific configuration (shell, execution path, etc). Item 4) is optional but it is very important
for good performances. We refer to the next section for a description of the various possibilities.




                                                26
```
