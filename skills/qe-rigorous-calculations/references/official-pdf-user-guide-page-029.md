# user_guide.pdf — page 29

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `5417b854455464f1e97778f11687676ce1f9aaee279e58603eb862da2a35a1e9`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    The directory for data is specified in input variables outdir and prefix (the former can
be specified as well in environment variable ESPRESSO TMPDIR): outdir/prefix.save. A
copy of pseudopotential files is also written there. If some processor cannot access the data
directory, the pseudopotential files are read instead from the pseudopotential directory specified
in input data. Unpredictable results may follow if those files are not the same as those in the
data directory!
    IMPORTANT: Avoid I/O to network-mounted disks (via NFS) as much as you can! Ideally
the scratch directory outdir should be a modern Parallel File System. If you do not have any,
you can use local scratch disks (i.e. each node is physically connected to a disk and writes to
it) but you may run into trouble anyway if you need to access your files that are scattered in
an unpredictable way across disks residing on different nodes.
    You can use input variable disk io to vary the amount of I/O done by pw.x. The default
value is disk io=’low’, so the code will store wavefunctions into RAM and not on disk during
the calculation. Specify disk io=’medium’ only if you have too many k-points and you run
into trouble with memory; choose disk io=’none’ if you do not need to keep final data files.

3.5    Tricks and problems
Trouble with parallel execution Always verify if your executable is actually compiled for
parallel execution or not: it is declared in the first lines of output. Running several instances
of a serial code with mpirun or mpiexec produces strange crashes.
    Many problems in parallel execution derive from the mixup of different MPI libraries and
runtime environments. There are two major MPI implementations, OpenMPI and MPICH,
coming in various versions, not necessarily compatible; plus vendor-specific implementations
(e.g. Intel MPI). A parallel machine may have multiple parallel compilers (typically, mpif90
scripts calling different serial compilers), multiple MPI libraries, multiple launchers for parallel
codes (different versions of mpirun and/or mpiexec).
    You have to figure out the proper combination of all of the above, which may require using
command module or manually setting environment variables and execution paths. What exactly
has to be done depends upon the configuration of your machine. You should inquire with your
system administrator or user support, if available; if not, YOU are the system administrator
and user support and YOU have to solve your problems.
    Please also note that while mysterious and irreproducible crashes in parallel execution may
be due to Quantum ESPRESSO bugs, more often than not they are a consequence of buggy
compilers or of buggy or miscompiled MPI libraries.

Trouble with input files Input files should be plain ASCII text. The presence of CRLF
line terminators (may appear as ˆM, Control-M, characters at the end of lines), tabulators, or
non-ASCII characters (e.g. non-ASCII quotation marks, that at a first glance may look the
same as the ASCII character) is a frequent source of trouble. Typically, this happens with
files coming from Windows or produced with ”smart” editors. Verify with command file and
convert with command iconv if needed.
     Some implementations of the MPI library have problems with input redirection in parallel.
This typically shows up under the form of mysterious errors when reading data. If this happens,
use the option -i (or -in, -inp, -input), followed by the input file name. Example:

   pw.x -i inputfile -nk 4 > outputfile


                                                29
```
