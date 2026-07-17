# user_guide.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `cb77276dae397ad26340e2641593b1e8fc70a4b44e51446a12c52b5276befef5`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   The Quantum Mobile virtual machine for Windows/Mac/Linux/Solaris provides a complete
Ubuntu Linux environment, containing Quantum ESPRESSO and much more. Link and
description in https://www.materialscloud.org/work/quantum-mobile.
   For source compilation, uncompress and unpack compressed archives in the typical .tar.gz
format using the command:
      tar zxvf qe-X.Y.Z.tar.gz
(a hyphen before ”zxvf” is optional) where X.Y.Z stands for the version number.
    A few additional packages that are not included in the base distribution will be downloaded
on demand at compile time, using either make or CMake (see Sec.2.7). Note however that this
will work only if the computer you are installing on is directly connected to the internet and
has either wget or curl installed and working. If you run into trouble, manually download each
required package into subdirectory archive/, not unpacking or uncompressing it: command
make will take care of this during installation.
    The Quantum ESPRESSO distribution contains several directories. Some of them are
common to all packages:
     Modules/        Fortran modules and utilities used by all programs
     upflib/         pseudopotential-related code, plus conversion tools
     include/        files *.h included by fortran and C source files
     FFTXlib/        FFT libraries
     LAXlib/         Linear Algebra (parallel) libraries
     KS Solvers/ Iterative diagonalization routines
     UtilXlib/       Miscellaneous timing, error handling, MPI utilites
     XClib/          Exchange-correlation functionals (excepted van der Waals)
     MBD/            Routines for many-body dispersions
     dft-d3/         Routines for DFT-D3 disesive corrections
     LR Modules/ Fortran modules and utilities used by linear-response codes
     install/        installation scripts and utilities
     pseudo/         pseudopotential files used by examples
     Doc/            general documentation
     external/       external libraries automatically downloaded
     test-suite/ automated tests
while others are specific to a single package:
     PW/       PWscf package
     EPW/      EPW package
     NEB/      PWneb package
     PP/       PostProc package
     PHonon/ PHonon package
     PWCOND/ PWcond package
     CPV/      CP package
     atomic/ atomic package
     GUI/      PWGui package
     HP/       HP package
     QEHeat/ QEHeat package
     KCW/      KCW package
  Finally, directory COUPLE/ contains code and documentation that is useful to call Quantum
ESPRESSO programs from external codes.

                                              8
```
