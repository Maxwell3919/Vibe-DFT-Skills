# user_guide.pdf — page 14

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `8710c7b472735b0ba98d3829cb0e12610560bdb031850c48661bfcd40f5bef1c`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
the LU code, plus the full storage Cholesky code. Follow the instructions in the ATLAS distri-
butions to produce a full LAPACK replacement. Also note that the ATLAS project appears
to be dead.
   Sergei Lisenkov reported success and good performances with optimized BLAS by Kazushige
Goto. The library is now available under an open-source license: see the GotoBLAS2 page at
http://www.openmathlib.org/OpenBLAS/.

2.5.2   FFT
The FFTXlib package of Quantum ESPRESSO contains a copy of an old FFTW library, but
also supports the newer FFTW3 library and some vendor-specific FFT libraries. It is strongly
recommanded to use FFT’s from an optimized library, such as e.g. those contained in Intel
MKL. configure will first search for vendor-specific FFT libraries; if none is found, it will
search for an external FFTW v.3 library; if none is found, it will fall back to the internal copy
of FFTW. configure will add the appropriate preprocessing options:

   • -D DFTI for DFTI (Intel MKL library),

   • -D FFTW3 for FFTW3 (external),

   • -D FFTW for FFTW (internal library),

   • -D LINUX ESSL for ESSL on IBM Linux machines (obsolete?),

   • -DASL for NEC ASL library on NEC machines (obsolete?),

to DFLAGS in the make.inc file. If you edit make.inc manually, please note that one and only
one among the mentioned preprocessing option must be set.
    If you have MKL libraries, you may either link FFTW3 from MKL, or use DFTI (recom-
mended).

2.5.3   MPI libraries
MPI libraries are needed for parallel execution, unless you are happy with OpenMP-only mul-
ticore parallelization. In well-configured machines, configure should find the appropriate par-
allel compiler for you, and this should find the appropriate libraries. If this does not happen,
see Sec.2.9.3.

2.5.4   HDF5
The HDF5 library (https://www.hdfgroup.org/downloads/hdf5/), v.1.8.16 or later, can be
used to perform binary I/O using the HDF5 format.
    If compiling the HDF5 library from sources, attention must be paid to pass options:
--enable-fortran, --enable-fortran2003, and --enable-parallel (see below), to the configure
script of HDF5 (not of Quantum ESPRESSO).
    To use HDF5 is usually sufficient to specify the path to the fortran compiler wrapper for
HDF5 (h5fc of h5pfc with the --with-hdf5= option of configure. If the wrapper is in the de-
fault path, just use --with-hdf5=yes. The configure script is usually able to extract the linker
options and the include directory path from the output of the wrapper. If it fails, the user can
provide configure options --with-hdf5-libs=<options> and --with-hdf5-include=<path>

                                               14
```
