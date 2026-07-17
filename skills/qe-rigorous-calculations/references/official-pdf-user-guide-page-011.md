# user_guide.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `cb7694cfda1998577ae52936d1ea7080e66da072487ffd1f30c2b7f4a8565bd8`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    Note that F90 is an “historical” name – we actually use Fortran 2008 – and that it should
be used only together with option --disable-parallel. This is because the value of F90 must
be consistent with the parallel Fortran compiler which is determined by configure and stored
in the MPIF90 variable.
    For example, the following command line:

        ./configure MPIF90=mpif90 FFLAGS="-O2 -assume byterecl" \
                     CC=gcc CFLAGS=-O3 LDFLAGS=-static

instructs configure to use mpif90 as Fortran compiler with flags -O2 -assume byterecl, gcc
as C compiler with flags -O3, and to link with flag -static. Note that the value of FFLAGS must
be quoted, because it contains spaces. NOTA BENE: passing the complete path to compilers
(e.g., F90=/path/to/f90xyz) may lead to obscure errors during compilation.

2.4.3    Supported architectures
Presently configure supports all ”common” computers, that is: based on Intel, AMD, ARM
CPUs, NVidia and (in a development branch) AMD GPUs, running Linux and (often but not
always) Mac OS X and MS-Windows. Quantum ESPRESSO works on many more kinds of
machines but may requires some tweaking, especially for the hardware of large HPC centers.
    If your machine type is unknown to configure, you may use the ARCH variable to suggest
an architecture among supported ones. Some parallel machines using a front-end may actually
need it, or else configure will correctly recognize the front-end but not the specialized compi-
lation environment of those machines. In some cases, cross-compilation requires to specify the
target machine with the --host option. This feature has not been extensively tested, but we
had at least one successful report (compilation for NEC SX6 on a PC). Currently supported
architectures are:
     x86 64         Intel and AMD 64-bit running Linux
     arm            ARM machines (with gfortran or armflang)
     craype         Cray machines using Cray PE
     mac686         Apple Intel machines running Mac OS X
     mingw32        Cross-compilation for MS-Windows, using mingw, 32 bits
     mingw64        As above, 64 bits
     cygwin         MS-Windows PCs with Cygwin
     ppc64*         Linux PowerPC machines, 64 bits
     ppc64-le*      as above, with IBM xlf compiler
     ppc64-bg*      IBM BlueGene
     ppc64-bgq* IBM BlueGene Q
     necsx*         NEC SX-6 and SX-8 machines
     ia32*          Intel 32-bit machines (x86) running Linux
     ia64*          Intel 64-bit (Itanium) running Linux
   Note: all architectures marked with a * are to be considered obsolescent or obsolete.

2.4.4    Command-line options
configure recognizes the following command-line options. Not all of them are implemented
for all compilers, though. Default value is between bracket:



                                              11
```
