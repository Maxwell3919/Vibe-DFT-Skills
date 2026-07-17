# 2.4 Building with make

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node11.html
- Retrieved: 2026-07-17T11:50:17+00:00
- Official source SHA-256: `9186d3cd49f411078d28400ee4f2162bde2136bacca3d17974ccc6ba7d860764`
- Extracted text SHA-256: `d19536ea10ddde799e8279a59417afeb5b2d1b729e9f0fe5b11cb56fadf6fecb`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2.5 Libraries

Up:

2 Installation

Previous:

2.3 Building with CMake

  

Contents

Subsections

2.4.1 Generalities

2.4.2 Environment variables

2.4.3 Supported architectures

2.4.4 Command-line options

2.4.5 
configure
for NVidia GPU's

2.4.6 Manual configuration

2.4 Building with 
make

2.4.1 Generalities

To build the Q
UANTUM 
ESPRESSO source package using 
make
, run the 
configure
script first. 
configure
will (try to) detect available compilers and libraries for
your machine, and set up things accordingly.

IMPORTANT: 
configure
will likely work only if your desired Fortran and 
C compilers are in your execution path, as specified in the PATH environment 
variable, and if the related system libraries can be reached (again,
as specified in suitable environment variables). Also, you may need to set 
environment variable OMPI_FC to the serial compiler you want, if you are
using 
mpif90
from OpenMPI. Most compiler suites come with a script
or a "module" file that properly defines all the needed environment variables. 

configure
supports out-of-source builds, i.e., it allows to compile the 
binaries in
directories other than the one containing the source tree. This is the preferred installation
method as it allows to build and manage different installations (eg cpu and gpu ones)
without duplicating the source code.

Instructions for the impatient:

cd qe-X.Y.Z/
mkdir build && cd build
../configure
make all

This will (try to) produce parallel (MPI) executable if a proper parallel
environment is detected, serial executables otherwise. For OpenMP executables,
specify 
./configure –enable-openmp
. For GPUs, see GPU-specific
instructions. Symlinks to executable programs appear in the 
build/bin/

subdirectory.

NB:
the usage of a 
build
directory, even though advised for, 
is not mandatory, the traditional build workflow

cd qe-X.Y.Z/
./configure
make all

is still supported.

configure
generates the following files in the build directory:

make.inc

compilation rules and flags (used by 
Makefile
)

configure.msg

a report of the configuration run (not needed for compilation)

config.log

detailed log of the configuration run (useful for debugging)

In addition, 
configure
generates (since v.7) files 
make.depend
,
containing dependencies upon modules, in the various subdirectories.
If you add/remove/move/rename modules, or change the list of objects
in any of the 
Makefile
's, run 
configure
again in
order to ensure that all 
Makefile
's and 
make.depend

are aligned to the current state of the distribution.

It is convenient to use "parallel make" to speed up compilation:

make -j [N]
compiles in parallel on N processors if N is
specified, on all available processors otherwise.

Note that if you interrupt 
make
while unpacking and compiling an external 
library, you may run into trouble the next time you type 
make
. 
If so, run 
make veryclean
, or even 
make distclean
, 
from the top directory, before running 
make
again.

You should always be able to compile the Q
UANTUM 
ESPRESSO suite
of programs without having to edit any of the generated files. However you
may have to tune 
configure
by specifying appropriate environment variables
and/or command-line options. Usually the tricky part is to get external
libraries recognized and used: see Sec.
2.5

for details and hints. In many cases, you may simply edit file

make.inc
. 

2.4.2 Environment variables

The behavior of 
configure
can be changed by defining some environment
variables. These can be set in any of these ways:

export VARIABLE=value; ./configure # sh, bash, ksh
setenv VARIABLE value; ./configure # csh, tcsh
env VARIABLE=value ./configure # any shell
./configure VARIABLE=value # any shell

Some environment variables that are relevant to 
configure
are:

ARCH

label identifying the machine type (see next section)

F90, CC

names of Fortran and C compilers

MPIF90

name of parallel Fortran 90 compiler (using MPI)

CPP

source file preprocessor (defaults to $CC -E)

LD

linker (defaults to $MPIF90)

(C,F,F90,CPP,LD)FLAGS

compilation/preprocessor/loader flags

LIBDIRS

extra directories where to search for libraries

IMPORTANT: as a rule, DO NOT DEFINE environment variables for 
configure
,
except those needed to have your compiler and libraries working.
Always try 
configure
with no further options as a first step,
unless you have a good reason to specify them.

Note that 
F90
is an ``historical'' name – we actually use
Fortran 2008 – and that it should be used only together with option

–disable-parallel
. This is because the value of F90 must be
consistent with the parallel Fortran compiler which is determined by

configure
and stored in the 
MPIF90
variable.

For example, the following command line:

./configure MPIF90=mpif90 FFLAGS="-O2 -assume byterecl" \
CC=gcc CFLAGS=-O3 LDFLAGS=-static

instructs 
configure
to use 
mpif90
as Fortran compiler
with flags 
-O2 -assume byterecl
, 
gcc
as C compiler with
flags 
-O3
, and to link with flag 
-static
.
Note that the value of 
FFLAGS
must be quoted, because it contains
spaces. NOTA BENE: passing the complete path to compilers (e.g.,

F90=/path/to/f90xyz
) may lead to obscure errors during
compilation.

2.4.3 Supported architectures

Presently 
configure
supports all "common" computers, that is: based on 
Intel, AMD, ARM CPUs, NVidia and (in a development branch) AMD GPUs, 
running Linux and (often but not always) Mac OS X and MS-Windows.
Q
UANTUM 
ESPRESSO works on many more kinds of machines but may requires some tweaking, 
especially for the hardware of large HPC centers.

If your machine type is unknown to 
configure
, you may use the

ARCH

variable to suggest an architecture among supported ones. Some 
parallel machines using a front-end may actually
need it, or else 
configure
will correctly recognize the front-end
but not the specialized compilation environment of those machines.
In some cases, cross-compilation requires to specify the target machine
with the 
–host
option. This feature has not been extensively
tested, but we had at least one successful report (compilation
for NEC SX6 on a PC). Currently supported architectures are:

x86_64

Intel and AMD 64-bit running Linux

arm

ARM machines (with gfortran or armflang)

craype

Cray machines using Cray PE

mac686

Apple Intel machines running Mac OS X

mingw32

Cross-compilation for MS-Windows, using mingw, 32 bits

mingw64

As above, 64 bits

cygwin

MS-Windows PCs with Cygwin

ppc64
*

Linux PowerPC machines, 64 bits

ppc64-le
*

as above, with IBM xlf compiler

ppc64-bg
*

IBM BlueGene

ppc64-bgq
*

IBM BlueGene Q

necsx
*

NEC SX-6 and SX-8 machines

ia32
*

Intel 32-bit machines (x86) running Linux

ia64
*

Intel 64-bit (Itanium) running Linux

Note
: all architectures marked with a * are to be considered
obsolescent or obsolete.

2.4.4 Command-line options

configure
recognizes the following command-line options.
Not all of them are implemented for all compilers, though. Default value
is between bracket:

–enable-parallel

compile for parallel (MPI) execution if possible (yes)

–enable-openmp

compile for OpenMP execution if possible (no)

–enable-static

produce static executables, arger but more portable (no)

–enable-shared

produce objects that are suitable for shared libraries (no)

–enable-debug

compile with debug flags (no)

–enable-pedantic

compile with gfortran pedantic flags on (no)

–enable-signals

enable signal trapping (no)

–enable-exit-status

enable returning exit status (no)

and the following optional packages:

–with-fox

Use official FoX library instead of built-in replacement (default:no)

–with-scalapack

(yes|no|intel) Use scalapack if available (default:yes)

 

Use 
intel
to force Intel MPI and BLACS (obsolescent)

–with-elpa-include

Specify full path of ELPA include and modules
headers (no)

–with-elpa-lib

Specify full path of the ELPA library (no)

–with-elpa-version

Specify ELPA API version: 2015 for ELPA releases 2015.x

 

and 2016.05; 2016 for ELPA releases 2016.11, 2017.x and

 

2018.05; 2018 for ELPA releases 2018.11 and beyond (2018)

–with-hdf5

(no | yes | 
<path>
)

 

Compile HDF5 support (no). If ``yes'', configure assumes a

 

valid v. > = 1.8.16 HDF5 installation with h5cc and h5fc in the

 

default executable search path. If 
<path>
is specified, it must be the

 

root folder of a standalone hdf5 installation.

–with-hdf5-libs

Specify the link options and libraries needed to link HDF5, if configure

 

fails to detect them. These options are usually composed by many

 

substrings and must be enclosed into quotes.

–with-hdf5-include

Specify full path the HDF5 include folder containing module and

 

headers files. Use it if configure fails to find the include folder.

–with-libxc

Enable support for the 
libxc
library (no)

–with-libxc-prefix

directory where 
libxc
is installed

–with-libxc-include

directory where 
libxc
Fortran headers reside

2.4.5 
configure
for NVidia GPU's

In order to compile the code for NVidia GPU's you need the NVidia HPC software
development kit (SDK). Beware: some versions may mis-compile Q
UANTUM 
ESPRESSO.
Ensure that all needed environmental variables
are properly defined, e.g. by running the "module" file provided in the HPC SDK with command

module
. Specify 
–with-cuda
and 
–with-cuda-cc
as explained 
below. Other options below
are optional. Enabling faster communications between GPUs, via NVlink or Infiniband RDMA, 
is essential for optimal parallel performance. 

The following 
configure
GPU options are available:

–with-cuda=value

enable compilation of GPU-accelerated subroutines.

 

value
should point the path where the CUDA toolkit

 

is installed, e.g. 
$NVHPC_CUDA_HOME

–with-cuda-cc=value

sets the compute capabilities for the compilation

 

of the accelerated subroutines.

 

value
must be consistent with the hardware and the

 

NVidia driver installed on the workstation or on the

 

compute nodes of the HPC facility (default: 35)

–with-cuda-runtime=value

(optional) sets the version of the CUDA toolkit used

 

for the compilation of the accelerated code.

 

value
must be consistent with the

 

CUDA Toolkit installed on the workstation

 

or available on the compute nodes of the HPC facility.

–with-cuda-mpi=value

yes
enables the usage of CUDA-aware MPI library.

 

Beware: if you have no fast inter-GPU communications, e.g.,

 

NVlink or Infiniband RDMA, you may get a crash at run time.

 

Important for optimal parallel performances (default: no).

–enable-nvtx=value

enable NVTX profiling (for developers, default: no).

To modify or extend 
configure
(advanced users only!), see the Wiki pages
on GitLab: 
https://gitlab.com/QEF/q-e/-/wikis
.

2.4.6 Manual configuration

If 
configure
stops before the end, and you don't find a way to fix
it, you have to write a working 
make.inc
file (optionally,

include/qe_cdefs.h
). The template used by 
configure
is

install/make.inc.in
and contains explanations of the meaning
of the various variables. Note that you may need
to select appropriate preprocessing flags
in conjunction with the desired or available
libraries (e.g. you need to add 
-D__FFTW
to 
DFLAGS

if you want to link internal FFTW). For a correct choice of preprocessing
flags, refer to the documentation in 
include/defs.h.README
.

Even if 
configure
works, you may need to tweak the 
make.inc

file. It is very simple, but please note that a) you must know what you are
doing, and b) if you change any settings
(e.g. preprocessing, compilation flags)
after a previous, successful or failed, compilation, you must run

make clean
before recompiling, unless you know exactly which
routines are affected by the changed settings and how to force their
recompilation. Running 
configure
again cleans objects and executables,
unless you use option 
–save
.

next 

up 

previous 

contents 

Next:

2.5 Libraries

Up:

2 Installation

Previous:

2.3 Building with CMake

  

Contents
```
