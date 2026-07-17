# user_guide.pdf — page 9

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `2e30c367077ffa57c761cd0326d8ce2dc8d785a60615ed20cd4b809bc5b397a2`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2.2     Prerequisites for source compilation
First of all, you need a minimal Unix environment: a command shell like bash or sh, utilities
make, awk, sed. Note that the scripts contained in the distribution assume that the local
language is set to the standard, i.e. ”C”; other settings may break them. Use export LC ALL=C
(sh/bash) or setenv LC ALL C (csh/tcsh) to prevent any problem when running those scripts.
    If you are not compiling a stable releasei from tarballs, you will also need git v.2.13 or later
to get the external libraries. You will need either CMake v.3.20 or later, or the configure
command from autoconf v. 2.64 or later.
    Second, you need a Fortran compiler compliant with F2008 standard and any half-decent
C compiler. For parallel execution, a parallel MPI-aware Fortran compiler and MPI libraries
implementing v.3 of the standard (notably, non-blocking broadcast and gather operations) are
required. For massively parallel machines, or for simple multicore parallelization, an OpenMP-
aware Fortran compiler and libraries are also required. To compile for NVidia GPUs you need
the NVidia HPC SDK (software development kit) v.21.7 or later, freely available for download.
    As a rule, Quantum ESPRESSO tries to keep compatibility with older compilers, avoiding
nonstandard extensions and newer features that are not widespread or stabilized. If however
your compiler is older than a few (∼ 5) years, it is likely that something will not work. The
same applies to mathematical and MPI libraries.
    Big computing centers typically provide a Fortran compiler complete with all needed li-
braries. Workstations or “commodity” machines using PC hardware, may or may not have
the needed software. If not, you may use the open-source gfortran compiler from the gcc dis-
tribution, and possibly open-source MPI libraries and run-time software. You may also get a
commercial compiler, some of which are available free of charge under some conditions (e.g.
academic or personal usage, no support) and may provide MPI libraries and run-time software
as well.

2.3     Building with CMake
See https://gitlab.com/QEF/q-e/-/wikis/Developers/CMake-build-system.

2.4     Building with make
2.4.1   Generalities
To build the Quantum ESPRESSO source package using make, run the configure script
first. This is actually a wrapper to the true configure, located in the install/ subdirectory
(configure -h for help). configure will (try to) detect available compilers and libraries for
your machine, and set up things accordingly.
    IMPORTANT: configure will likely work only if your desired Fortran and C compilers
are in your execution path, as specified in the PATH environment variable, and if the related
system libraries can be reached (again, as specified in suitable environment variables). Also,
you may need to set environment variable OMPI FC to the serial compiler you want, if you are
using mpif90 from OpenMPI. Most compiler suites come with a script or a ”module” file that
properly defines all the needed environment variables.
    Instructions for the impatient:

      cd qe-X.Y.Z/


                                                 9
```
