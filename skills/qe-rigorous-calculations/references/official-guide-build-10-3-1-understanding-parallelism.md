# 3.1 Understanding Parallelism

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node18.html
- Retrieved: 2026-07-17T11:50:27+00:00
- Official source SHA-256: `6597f94334064fc41273c1cca8efeb1248308fa37f36ff12a06504fa9bc5e9f4`
- Extracted text SHA-256: `bbe66812d975aaa1d4bf7adadcb6b4727320169430626fe498dd619e809d1e5c`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.2 Running on parallel machines

Up:

3 Parallelism

Previous:

3 Parallelism

  

Contents

3.1 Understanding Parallelism

Two different parallelization paradigms are currently implemented
in Q
UANTUM 
ESPRESSO:

Message-Passing (MPI)
. A copy of the executable runs
on each CPU; each copy lives in a different world, with its own
private set of data, and communicates with other executables only
via calls to MPI libraries. MPI parallelization requires compilation
for parallel execution, linking with MPI libraries, execution using
a launcher program (depending upon the specific machine). The number
of CPUs used
is specified at run-time either as an option to the launcher or
by the batch queue system.

OpenMP
. A single executable spawn subprocesses
(threads) that perform in parallel specific tasks.
OpenMP can be implemented via compiler directives (
explicit

OpenMP) or via 
multithreading
libraries (
library
OpenMP).
Explicit OpenMP require compilation for OpenMP execution;
library OpenMP requires only linking to a multithreading
version of the mathematical libraries.
The number of threads is specified at run-time in the environment
variable OMP_NUM_THREADS.

MPI is the well-established, general-purpose parallelization.
In Q
UANTUM 
ESPRESSO several parallelization levels, specified at run-time
via command-line options to the executable, are implemented
with MPI. This is your first choice for execution on a parallel
machine.

The support for explicit OpenMP is steadily improving.
Explicit OpenMP can be used together with MPI and also
together with library OpenMP. Beware
conflicts between the various kinds of parallelization!
If you don't know how to run MPI processes
and OpenMP threads in a controlled manner, forget about mixed
OpenMP-MPI parallelization.

next 

up 

previous 

contents 

Next:

3.2 Running on parallel machines

Up:

3 Parallelism

Previous:

3 Parallelism

  

Contents
```
