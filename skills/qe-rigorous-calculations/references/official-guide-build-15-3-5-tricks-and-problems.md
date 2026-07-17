# 3.5 Tricks and problems

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node22.html
- Retrieved: 2026-07-17T11:50:35+00:00
- Official source SHA-256: `e4ac8da0253b33ca6541e7645f86b8bf91adbdf8f397ad417daf278c932e95aa`
- Extracted text SHA-256: `b17d0afcbc5cd138b79412c05d86a5798d3e90748064413d518172c81ad6b414`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

About this document ...

Up:

3 Parallelism

Previous:

3.4 Understanding parallel I/O

  

Contents

Subsections

3.5.0.1 Trouble with parallel execution

3.5.0.2 Trouble with input files

3.5.0.3 Trouble with MPI-OpenMP parallelization

3.5 Tricks and problems

3.5.0.1 Trouble with parallel execution

Always verify if your executable is actually compiled for
parallel execution or not: it is declared in the first lines
of output. Running several instances of a serial code with

mpirun
or 
mpiexec
produces strange crashes.

Many problems in parallel execution derive from the mixup of different
MPI libraries and runtime environments. There are two major MPI
implementations, OpenMPI and MPICH, coming in various versions,
not necessarily compatible; plus vendor-specific implementations
(e.g. Intel MPI). A parallel machine may have multiple parallel
compilers (typically, 
mpif90
scripts calling different
serial compilers), multiple MPI libraries, multiple launchers
for parallel codes (different versions of 
mpirun
and/or

mpiexec
). 

You have to figure out the proper combination
of all of the above, which may require using command 
module

or manually setting environment variables and execution paths.
What exactly has to be done depends upon the configuration of your
machine. You should inquire with your system administrator or user
support, if available; if not, YOU are the system administrator
and user support and YOU have to solve your problems.

Please also note that while mysterious and irreproducible crashes
in parallel execution may be due to Q
UANTUM 
ESPRESSO bugs, more often than not 
they are a consequence of buggy compilers or of buggy or miscompiled 
MPI libraries.

3.5.0.2 Trouble with input files

Input files should be plain ASCII text. The presence of CRLF line 
terminators (may appear as ˆM, Control-M, characters at the end
of lines), tabulators, or non-ASCII characters (e.g. non-ASCII
quotation marks, that at a first glance may look the same as
the ASCII character) is a frequent source of trouble.
Typically, this happens with files coming from Windows or produced
with "smart" editors. Verify with command 
file
and convert
with command 
iconv
if needed.

Some implementations of the MPI library have problems with input
redirection in parallel. This typically shows up under the form of
mysterious errors when reading data. If this happens, use the option

-i
(or 
-in
, 
-inp
, 
-input
),
followed by the input file name.
Example:

pw.x -i inputfile -nk 4 > outputfile

Of course the
input file must be accessible by the processor that must read it
(only one processor reads the input file and subsequently broadcasts
its contents to all other processors).

Apparently the LSF implementation of MPI libraries manages to ignore or to
confuse even the 
-i/in/inp/input
mechanism that is present in all
Q
UANTUM 
ESPRESSO codes. In this case, use the 
-i
option of 
mpirun.lsf

to provide an input file.

3.5.0.3 Trouble with MPI-OpenMP parallelization

It is often advantageous to compile for both MPI and OpenMP parallelization,
taking advantage of both. If however you get really bad performances, you 
may have run into a conflict between the two parallelizations, leading to
more than one thread trying to access the same core.

Q
UANTUM 
ESPRESSO cannot control where MPI processes and OpenMP thread execute:
this is something that the operating system should know about. 
All you can control is the number of MPI processes (with 
mpirun
)
and of OpenMP threads per MPI process (with the environment variable
OMP_NUM_THREADS=N). If you are out of luck and of better ideas, just set
OMP_NUM_THREADS=1,

next 

up 

previous 

contents 

Next:

About this document ...

Up:

3 Parallelism

Previous:

3.4 Understanding parallel I/O

  

Contents
```
