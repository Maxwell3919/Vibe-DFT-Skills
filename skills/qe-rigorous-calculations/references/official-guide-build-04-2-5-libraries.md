# 2.5 Libraries

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node12.html
- Retrieved: 2026-07-17T11:50:19+00:00
- Official source SHA-256: `e221d698087b75c5198bbfe3568d7b2da5183527eb2c2d88e9f5b92b229f16ce`
- Extracted text SHA-256: `0f02549e7c760c1a75b16a5dfa5a776dd66d7befff8bf5fcbd0336883ce66aee`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

2.6 Libxc library

Up:

2 Installation

Previous:

2.4 Building with make

  

Contents

Subsections

2.5.1 BLAS and LAPACK

2.5.2 FFT

2.5.3 MPI libraries

2.5.4 HDF5

2.5.5 Other libraries

2.5.6 In case of trouble

2.5 Libraries

2.5.1 BLAS and LAPACK

Q
UANTUM 
ESPRESSO needs the BLAS and LAPACK mathematical libraries.
As a rule, one should always use vendor-specific optimized 
BLAS and LAPACK, such as e.g. those found in Intel's MKL. 
They often yield huge performance gains with respect to 
compiled libraries. 
configure
always try to locate the 
best mathematical libraries.

If optimized BLAS and LAPACK are not available, Q
UANTUM 
ESPRESSO automatically 
downloads and compiles them. Another option is to try the ATLAS library: 

http://math-atlas.sourceforge.net/
.
Note that ATLAS is not a complete replacement for LAPACK: it contains
all of the BLAS, plus the LU code, plus the full storage Cholesky code.
Follow the instructions in the ATLAS distributions to produce a full 
LAPACK replacement. Also note that the ATLAS project appears to be dead.

Sergei Lisenkov reported success and good performances with optimized
BLAS by Kazushige Goto. The library is now available under an
open-source license: see the GotoBLAS2 page at 

http://www.openmathlib.org/OpenBLAS/
.

2.5.2 FFT

The FFTXlib package of Q
UANTUM 
ESPRESSO contains a copy of an old FFTW library,
but also supports the newer FFTW3 library and some vendor-specific 
FFT libraries. It is strongly recommanded to use FFT's from an
optimized library, such as e.g. those contained in Intel MKL.

configure
will first search for vendor-specific FFT libraries;
if none is found, it will search for an external FFTW v.3 library;
if none is found, it will fall back to the internal copy of FFTW.

configure
will add the appropriate preprocessing options:

-D__DFTI
for DFTI (Intel MKL library),

-D__FFTW3
for FFTW3 (external),

-D__FFTW
for FFTW (internal library),

-D__LINUX_ESSL
for ESSL on IBM Linux machines (obsolete?),

-DASL
for NEC ASL library on NEC machines (obsolete?),

to 
DFLAGS
in the 
make.inc
file.
If you edit 
make.inc
manually, please note that one and
only one among the mentioned preprocessing option must be set.

If you have MKL libraries, you may either link FFTW3 from MKL,
or use DFTI (recommended).

2.5.3 MPI libraries

MPI libraries are needed for parallel execution, unless you are
happy with OpenMP-only multicore parallelization.
In well-configured machines, 
configure
should find the appropriate
parallel compiler for you, and this should find the appropriate
libraries. If this does not happen, see Sec.
2.9.3
.

2.5.4 HDF5

The HDF5 library (
https://www.hdfgroup.org/downloads/hdf5/
),
v.1.8.16 or later, can be used to perform binary I/O using the HDF5
format.

If compiling the HDF5 library from sources, attention must be paid
to pass options:

–enable-fortran
, 
–enable-fortran2003
, and 

–enable-parallel
(see below),
to the 
configure
script of 
HDF5
(not of Q
UANTUM 
ESPRESSO).

To use HDF5 is usually sufficient to specify the path to the fortran
compiler wrapper for HDF5 (
h5fc
of 
h5pfc
with the

–with-hdf5=
option of configure. If the wrapper is in the
default path, just use 
–with-hdf5=yes
.
The configure script is usually able to extract the linker options
and the include directory path from the output of the wrapper. If it
fails, the user can provide configure options

–with-hdf5-libs=<options>
and 
–with-hdf5-include=<path>

for the linker options and include path respectively.
These options are often needed when using the HDF5 packages
provided by many LINUX distributions. In this case you may first try
the 
–with-hdf5=yes
option. If it fails, just type command

h5fc –show
(or 
h5pfc
if you are using parallel HDF5):
the command will print out the linker and include options to be passed
manually to the configure script.

The configure script is able to determine whether one is linking to a
serial or parallel HDF5 library, and will set the flag

-D__HDF5_SERIAL
in the 
make.inc
file accordingly.

2.5.5 Other libraries

The accelerated version of the code for NVidia GPU's uses standard CUDA 
libraries 
cublas, cufft, curand, cusolver
that are available 
from the NVidia HPC SDK and found by 
configure
.

If the appropriate 
configure
option is set, the code downloads and compile 
the FoX library (
m4
is required in this case) for reading and writing
xml files. This option is useful only for debugging. 

Q
UANTUM 
ESPRESSO can use the MASS vector math library from IBM, but for a single routine
and only with the XLF compiler, so it is hardly worth it.

2.5.6 In case of trouble

The 
configure
script attempts to find optimized libraries, but may fail
if they have been installed in non-standard places. You should examine
the final value of 
BLAS_LIBS, LAPACK_LIBS, FFT_LIBS, MPI_LIBS
(if needed), either in the output of 
configure
or in the generated

make.inc
, to check whether it found all the libraries that you intend to use.

If some library was not found, you can specify a list of directories to search
in the environment variable 
LIBDIRS
,
and rerun 
configure
; directories in the
list must be separated by spaces. For example:

./configure LIBDIRS="/opt/intel/oneapi/mkl /usr/lib/math"

If this still fails, you may set some or all of the 
*_LIBS
variables manually
and retry. For example:

./configure BLAS_LIBS="-L/usr/lib/math -lf77blas -latlas_sse"

Beware that in this case, 
configure
will blindly accept the specified value,
and won't do any check or extra search.

next 

up 

previous 

contents 

Next:

2.6 Libxc library

Up:

2 Installation

Previous:

2.4 Building with make

  

Contents
```
