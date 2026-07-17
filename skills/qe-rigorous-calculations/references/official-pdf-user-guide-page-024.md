# user_guide.pdf — page 24

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `7d551d4d4941923eb0804c2c5834c13aecc9673b0267df1f255560cf823234d1`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
provided by PGI (the configure of FoX fails: use script install/build fox with pgi.sh to
manually compile FoX).
    Another option: use MinGW/MSYS. Download the installer from https://osdn.net/projects/min
install MinGW, MSYS, gcc and gfortran. Start a shell window; run ”./configure”; edit make.inc;
uncommenting the second definition of TOPDIR (the first one introduces a final ”/” that Win-
dows doesn’t like); run ”make”. Note that on some Windows the code fails when checking that
tmp dir is writable, for unclear reasons.
    Another option is Cygwin, a UNIX environment which runs under Windows: see
http://www.cygwin.com/.

2.9.5   Mac OS
Mac OS-X machines with gfortran, and possibly other compilers as well, should in principle
work, but ”your mileage may vary”, depending upon the specific software stack you are using.
Parallel compilation with OpenMPI should also work.
   Gfortran information and binaries for Mac OS-X here: http://hpc.sourceforge.net/.
   If you get an error like

  clang: error: no input files
  make[1]: *** [laxlib.fh] Error 1
  make: *** [libla] Error 1i

redefine CPP as CPP=gcc -E in make.inc.
   Mysterious crashes in zdotc are due to a known incompatibility of complex functions with
some optimized BLAS. They should no longer be an issue, as all zdotc have been replaced
from the current Quantum ESPRESSO version.
   ”I have had some success compiling pw.x on the newish apple hardware. Running run-tests-
pw-parallel resulted in all but 3 tests passed (3 unknown). QE6.7 works out of the box:

   • Install homebrew

   • Using homebrew install gcc (11.2.0), open-mpi (4.1.1 2), fftw3 (3.3.10), and veclibfort
     (0.4.2 7)

To configure QE:

./configure FC=mpif90 CC=mpicc CPP=cpp-11 BLAS_LIBS="-L/opt/homebrew/lib
           -lveclibfort" LIBDIRS=/opt/homebrew/lib

Current develop branch needed two changes:

  1. The script external/devxlib/config/config.sub is outdated, and needs to be adjusted
     to correctly parse the machine information. I pulled a more up-to-date version from
     iains/gcc-darwin-arm64 github repo


  2. PW/src/efermig.f90 needed to be compiled without optimization -O0. No idea why at
     the moment.”

(Info by John Vinson, NIST, )


                                             24
```
