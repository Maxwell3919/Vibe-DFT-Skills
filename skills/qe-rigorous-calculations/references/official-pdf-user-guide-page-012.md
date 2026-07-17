# user_guide.pdf — page 12

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `726106fe8dbed68af144dd1cafa0287ad86aa4cf40665d31845555063b30540e`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 --enable-parallel         compile for parallel (MPI) execution if possible (yes)
 --enable-openmp           compile for OpenMP execution if possible (no)
 --enable-static           produce static executables, arger but more portable (no)
 --enable-shared           produce objects that are suitable for shared libraries (no)
 --enable-debug            compile with debug flags (no)
 --enable-pedantic         compile with gfortran pedantic flags on (no)
 --enable-signals          enable signal trapping (no)
 --enable-exit-status      enable returning exit status (no)
and the following optional packages:
 --with-fox                Use official FoX library instead of built-in replacement (default:no)
 --with-scalapack          (yes|no|intel) Use scalapack if available (default:yes)
                           Use intel to force Intel MPI and BLACS (obsolescent)
 --with-elpa-include       Specify full path of ELPA include and modules headers (no)
 --with-elpa-lib           Specify full path of the ELPA library (no)
 --with-elpa-version       Specify ELPA API version: 2015 for ELPA releases 2015.x
                           and 2016.05; 2016 for ELPA releases 2016.11, 2017.x and
                           2018.05; 2018 for ELPA releases 2018.11 and beyond (2018)
 --with-hdf5               (no | yes | <path>)
                           Compile HDF5 support (no). If “yes”, configure assumes a
                           valid v. >= 1.8.16 HDF5 installation with h5cc and h5fc in the
                           default executable search path. If <path> is specified, it must be the
                           root folder of a standalone hdf5 installation.
 --with-hdf5-libs          Specify the link options and libraries needed to link HDF5, if configure
                           fails to detect them. These options are usually composed by many
                           substrings and must be enclosed into quotes.
 --with-hdf5-include       Specify full path the HDF5 include folder containing module and
                           headers files. Use it if configure fails to find the include folder.
 --with-libxc              Enable support for the libxc library (no)
 --with-libxc-prefix       directory where libxc is installed
 --with-libxc-include directory where libxc Fortran headers reside

2.4.5   configure for NVidia GPU’s
In order to compile the code for NVidia GPU’s you need the NVidia HPC software development
kit (SDK). Beware: some versions may mis-compile Quantum ESPRESSO. Ensure that
all needed environmental variables are properly defined, e.g. by running the ”module” file
provided in the HPC SDK with command module. Specify --with-cuda and --with-cuda-cc
as explained below. Other options below are optional. Enabling faster communications between
GPUs, via NVlink or Infiniband RDMA, is essential for optimal parallel performance.
    The following configure GPU options are available:




                                              12
```
