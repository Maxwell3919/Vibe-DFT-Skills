# 2.9 Installation tricks and problems

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node16.html
- Retrieved: 2026-07-17T11:50:24+00:00
- Official source SHA-256: `25daed7acc2661cd0af4c0926fda742c7596d4a09ad1ea8421eb7124dcbe79e3`
- Extracted text SHA-256: `ad2ec16097266aa1974bb0034b4e945c0d22925054056cfd2648ef16ca6ef7c4`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3 Parallelism

Up:

2 Installation

Previous:

2.8 Running tests and examples

  

Contents

Subsections

2.9.1 All architectures

2.9.2 Linux PC's

2.9.2.1 Linux PCs with Intel compiler (ifx, ifort)

2.9.2.2 Linux PCs with MKL libraries

2.9.2.3 Linux PCs with AMD processors

2.9.3 Linux PC clusters with MPI

2.9.4 Microsoft Windows

2.9.5 Mac OS

2.9.6 Cray machines

2.9 Installation tricks and problems

2.9.1 All architectures

Working Fortran and C compilers must be present in your PATH.
If 
configure
says that you have no working compiler, well,
you have no working compiler, at least not in your PATH, and
not among those recognized by 
configure
.

If you get 
Compiler Internal Error
or similar messages: your
compiler version is buggy. Try to lower the optimization level, or to
remove optimization just for the routine that has problems. If it
doesn't work, or if you experience weird problems at run time, try to
install patches for your version of the compiler (most vendors release
at least a few patches for free), or to upgrade to a more recent
compiler version.

If you get error messages at the loading phase that look like

file XYZ.o: unknown / not recognized/ invalid / wrong
file type / file format / module version
,
one of the following things have happened:

you have leftover object files from a compilation with another
compiler: run 
make clean
and recompile.

make
did not stop at the first compilation error (it may
happen in some software configurations). Remove the file *.o
that triggers the error message, recompile, look for a
compilation error.

If many symbols are missing in the loading phase: you did not specify the
location of all needed libraries (LAPACK, BLAS, FFTW, machine-specific
optimized libraries), in the needed order. If system libraries are missing, 
the problem is in your compiler/library combination or in their usage, not 
in Q
UANTUM 
ESPRESSO.

If you get 
Segmentation fault
or similar errors
in the provided tests and examples: your compiler, or
your mathematical libraries, or MPI libraries,
or a combination thereof, is buggy, or there is some
software incompatibility. Although one can never rule out
the presence of subtle bugs in Q
UANTUM 
ESPRESSO that are not revealed during
the testing phase, it is very unlikely
that this happens on the provided tests and examples.

If all test fails, look into the output and error files:
there is some dumb reason for failure.

If most test pass but some fail, again: look into the output
and error files.

2.9.2 Linux PC's

Both AMD and Intel CPUs, 32-bit and 64-bit, are supported and work,
either in 32-bit emulation and in 64-bit mode. 64-bit executables
can address a much larger memory space than 32-bit executable, but
there is no gain in speed.
Beware: the default integer type for 64-bit machine is typically
32-bit long. You should be able to use 64-bit integers as well,
but it is not guaranteed to work and will not give
any advantage anyway.

It is usually convenient to create semi-statically linked executables (with only
libc, libm, libpthread dynamically linked). If you want to produce a binary
that runs on different machines, compile it on the oldest machine you have
(i.e. the one with the oldest version of the operating system).

Currently, configure supports, and Q
UANTUM 
ESPRESSO works with, not-too-old and
not-too-buggy versions of gfortran, Intel (ifx, ifort), NVidia (nvfortran), 
AMD (AOCC v.5), ARM (armflang), Cray (ftn) compilers.

2.9.2.1 Linux PCs with Intel compiler (ifx, ifort)

If 
configure
doesn't find the compiler, or if you get

Error loading shared libraries
at run time, you may have
forgotten to execute the script that
sets up the correct PATH and library path. Unless your system manager has
done this for you, you should execute the appropriate script – located in
the directory containing the compiler executable – in your
initialization files. Consult the documentation provided by Intel.

2.9.2.2 Linux PCs with MKL libraries

On Intel CPUs it is very convenient to use Intel MKL libraries
(freely available together with the Intel compiler at

https://software.intel.com
). They can be used also 
with non-Intel compilers. With gfortran, one has to link 

-lmkl_gf_lp64
instead of 
-lmkl_intel_lp64

(
configure
should take care of it).

configure
properly detects MKL libraries,
as long as the $MKLROOT environment variable is set in the current shell.
Normally this environment variable is set by sourcing the environment script
provided by Intel.

By default the non-threaded version of MKL is linked, unless option

configure –with-openmp
is specified. In case of trouble,
refer to the following web page to find the correct way to link MKL:

http://software.intel.com/en-us/articles/intel-mkl-link-line-advisor/
.

For parallel (MPI) execution on multiprocessor (SMP) machines, set the
environment variable OMP_NUM_THREADS to 1 unless you know how to run
MPI+OpenMP. See Sec.
3
for more info on this
and on the difference between MPI and OpenMP parallelization.

2.9.2.3 Linux PCs with AMD processors

For AMD CPUs there are optimized libraries called AOCL, AMD Optimizing CPU 
Libraries, bundled with the AOCC v.5 compiler, freely available from AMD.

`` Recently I played around with some AMD EPYC cpus and the bad thing
is that I also saw some strange numbers when using libflame/aocl 2.1.
(...) Since version 2020 the MKL performs rather well when using AMD cpus,
however, if you want to get the best performance you have to additionally set:

export MKL_DEBUG_CPU_TYPE=5

which gives an additional 10-20% speedup with MKL 2020,
while for earlier versions the speedup is greater than 200%.
[...] Another note, there seem to be problems using FFTW interface
of MKL with AMD cpus. To get around this problem, one has to
additionally set

export MKL_CBWR=AUTO

`` (Info by Tobias Klöffel, Feb. 2020)

2.9.3 Linux PC clusters with MPI

PC clusters running some version of MPI are a very popular
computational platform nowadays. Q
UANTUM 
ESPRESSO is known to work
with at least the MPICH2 and OpenMPI implementations.

configure
should automatically recognize a properly installed
parallel environment and prepare for parallel compilation.
Unfortunately this not always happens. In fact:

configure
tries to locate a parallel compiler in a logical
place with a logical name, but if it has a strange names or it is
located in a strange location, you will have to instruct 
configure
to find it. If there is no parallel Fortran compiler (e.g., mpif90),
you will have to install one.

configure
tries to locate libraries (both mathematical and
parallel libraries) in the usual places with usual names, but if
they have strange names or strange locations, you will have to
rename/move them, or to instruct 
configure
to find them. If MPI
libraries are not found, parallel compilation is disabled.

configure
tests that the compiler and the libraries are
compatible (i.e. the compiler may link the libraries without
conflicts and without missing symbols). If they aren't and the
compilation fails, 
configure
will revert to serial compilation.

Apart from such problems, Q
UANTUM 
ESPRESSO compiles and works on all non-buggy, properly
configured hardware and software combinations. In some cases you may have to
recompile MPI libraries: not all MPI installations contain support for
the Fortran compiler of your choice (or for any Fortran compiler
at all).

If Q
UANTUM 
ESPRESSO does not work for some reason on a PC cluster,
try first if it works in serial execution. A frequent problem with parallel
execution is that Q
UANTUM 
ESPRESSO does not read from standard input,
due to the configuration of MPI libraries: see Sec.
3.5
.
If you are dissatisfied with the performances in parallel execution,
see Sec.
3
and in particular Sec.
3.5
.

2.9.4 Microsoft Windows

Currently the safest way to build Q
UANTUM 
ESPRESSO on Windows is to enable the
Windows Subsystem for Linux (WSL) v.2, available on Windows 10 and 11.
You may install a Linux distribution you like and compile as on Linux. 
It works very well. See here:

https://learn.microsoft.com/en-us/windows/wsl/install

Another option is Quantum Mobile:

https://www.materialscloud.org/work/quantum-mobile
.

If you prefere a native Windows build, you are welcome to try 
the various possibilities listed below and to report details
in case of success.

Since February 2020 Q
UANTUM 
ESPRESSO can be compiled on MS-Windows 10 using PGI 19.10
Community Edition (freely downloadable). 
configure
works with the bash
script provided by PGI (the 
configure
of FoX fails: use script

install/build_fox_with_pgi.sh
to manually compile FoX).

Another option: use MinGW/MSYS. Download the installer from

https://osdn.net/projects/mingw/
, install MinGW, MSYS, gcc and
gfortran. Start a shell window; run "./configure"; edit 
make.inc
;
uncommenting the second definition of TOPDIR (the first one introduces a
final "/" that Windows doesn't like); run "make". Note that on some Windows
the code fails when checking that 
tmp_dir
is writable, for unclear
reasons.

Another option is Cygwin, a UNIX environment which runs under Windows: see

http://www.cygwin.com/
.

2.9.5 Mac OS

Mac OS-X machines with gfortran, and possibly other compilers as well,
should in principle work, but "your mileage may vary", depending upon 
the specific software stack you are using. Parallel compilation with 
OpenMPI should also work.

Gfortran information and binaries for Mac OS-X here:

http://hpc.sourceforge.net/
.

If you get an error like

clang: error: no input files
make[1]: *** [laxlib.fh] Error 1
make: *** [libla] Error 1i

redefine 
CPP
as 
CPP=gcc -E
in 
make.inc
.

Mysterious crashes in 
zdotc
are due to a known incompatibility of
complex functions with some optimized BLAS. They should no longer be an
issue, as all 
zdotc
have been replaced from the current Q
UANTUM 
ESPRESSO version.

"I have had some success compiling pw.x on the newish apple hardware.
Running run-tests-pw-parallel resulted in all but 3 tests passed (3 unknown).
QE6.7 works out of the box:

Install homebrew

Using homebrew install gcc (11.2.0), open-mpi (4.1.1_2), 
fftw3 (3.3.10), and veclibfort (0.4.2_7)

To configure QE: 

./configure FC=mpif90 CC=mpicc CPP=cpp-11 BLAS_LIBS="-L/opt/homebrew/lib
-lveclibfort" LIBDIRS=/opt/homebrew/lib

Current develop branch needed two changes:

The script external/devxlib/config/config.sub is outdated, 
and needs to be adjusted to correctly parse the machine information. 
I pulled a more up-to-date version from iains/gcc-darwin-arm64 github repo

PW/src/efermig.f90 needed to be compiled without optimization -O0. 
No idea why at the moment."

(Info by John Vinson, NIST, )

2.9.6 Cray machines

Cray machines may be tricky:
''... despite what people can imagine, every CRAY machine deployed can
have different environment. For example on the machine I usually use
for tests [...] I do have to unload some modules to make QE running
properly. On another CRAY [...] there is also Intel compiler as option
and the system is slightly different compared to the other.'' 
(info by Filippo Spiga)

./configure ARCH=craype
should work for recent Cray machines.
This selects the 
ftn
compiler, that typically uses
the 
crayftn
compiler but may also use other ones,
depending upon the site and personal environment. 
ftn
v.15.0.1
and later should compile QE properly. Some compiler versions may however
run into problems like these for 
ftn
v.14.0.3:

internal compiler error in 
esm_stres_mod.f90
;

crashes when writing the final xml data file.

Workaround: compile codes 
esm_stres_mod.f90
,

Modules/qexsd*.f90
, 
PW/src/pw_restart_new.f90

with reduced optimization, using -O0 or -O1 instead of the default
-O3,fp3 optimization.

If you want to use the Intel compiler instead, try something like:

$ module swap PrgEnv-cray PrgEnv-intel
$ ./configure ARCH=craype [--enable-openmp --enable-parallel --with-scalapack]

next 

up 

previous 

contents 

Next:

3 Parallelism

Up:

2 Installation

Previous:

2.8 Running tests and examples

  

Contents
```
