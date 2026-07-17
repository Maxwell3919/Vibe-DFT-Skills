# user_guide.pdf — page 15

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `93eadf61c126ffd9c41948c15ee2e4fa498114ab48fa9fcdc45495027640a270`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
for the linker options and include path respectively. These options are often needed when using
the HDF5 packages provided by many LINUX distributions. In this case you may first try the
--with-hdf5=yes option. If it fails, just type command h5fc --show (or h5pfc if you are
using parallel HDF5): the command will print out the linker and include options to be passed
manually to the configure script.
    The configure script is able to determine whether one is linking to a serial or parallel HDF5
library, and will set the flag -D HDF5 SERIAL in the make.inc file accordingly.

2.5.5   Other libraries
The accelerated version of the code for NVidia GPU’s uses standard CUDA libraries cublas,
cufft, curand, cusolver that are available from the NVidia HPC SDK and found by configure.
   If the appropriate configure option is set, the code downloads and compile the FoX library
(m4 is required in this case) for reading and writing xml files. This option is useful only for
debugging.
   Quantum ESPRESSO can use the MASS vector math library from IBM, but for a single
routine and only with the XLF compiler, so it is hardly worth it.

2.5.6   In case of trouble
The configure script attempts to find optimized libraries, but may fail if they have been in-
stalled in non-standard places. You should examine the final value of BLAS LIBS, LAPACK LIBS,
FFT LIBS, MPI LIBS (if needed), either in the output of configure or in the generated make.inc,
to check whether it found all the libraries that you intend to use.
    If some library was not found, you can specify a list of directories to search in the envi-
ronment variable LIBDIRS, and rerun configure; directories in the list must be separated by
spaces. For example:

   ./configure LIBDIRS="/opt/intel/oneapi/mkl /usr/lib/math"

If this still fails, you may set some or all of the * LIBS variables manually and retry. For
example:

   ./configure BLAS_LIBS="-L/usr/lib/math -lf77blas -latlas_sse"

Beware that in this case, configure will blindly accept the specified value, and won’t do any
check or extra search.

2.6     Libxc library
Quantum ESPRESSO is compatible with libxc version 4.3.0 or later (compatibility with
older versions is not guaranteed).
The libxc functionals are available for LDA, GGA and metaGGA, however, not all of them
are straightforwardly usable. Some of them may depend on specific external parameters and
some others may provide as output the energy or the potential, but not both. Therefore some
attention has to be paid when using libxc. Warning messages should appear in the output
when particular cases whose correct operation in Quantum ESPRESSO is not guaranteed
are chosen.


                                               15
```
