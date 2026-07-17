# user_guide.pdf — page 10

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `6f9df189b09aea56583e6419c8a1b916b38ed1c4aee55090af221a715d7c373d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    ./configure
     make all

This will (try to) produce parallel (MPI) executable if a proper parallel environment is detected,
serial executables otherwise. For OpenMP executables, specify ./configure --enable-openmp.
For GPUs, see GPU-specific instructions. Symlinks to executable programs appear in the bin/
subdirectory.
configure generates the following files:
     make.inc                     compilation rules and flags (used by Makefile)
     install/configure.msg a report of the configuration run (not needed for compilation)
     install/config.log           detailed log of the configuration run (useful for debugging)
     include/configure.h          optional: info on compilation flags (to enable it, uncomment
                                  #define __HAVE_CONFIG_INFO in Modules/environment.f90)
In addition, configure generates (since v.7) files make.depend, containing dependencies upon
modules, in the various subdirectories. If you add/remove/move/rename modules, or change
the list of objects in any Makefile, type make depend, or run ./install/makedeps.sh, to
update files make.depend.
    It is convenient to use ”parallel make” to speed up compilation: make -jN compiles in
parallel on N processors. Note that if you interrupt make while unpacking and compiling an
external library, you may run into trouble the next time you type make. If so, run make
veryclean, or even make distclean, before running make again.
    You should always be able to compile the Quantum ESPRESSO suite of programs without
having to edit any of the generated files. However you may have to tune configure by specifying
appropriate environment variables and/or command-line options. Usually the tricky part is to
get external libraries recognized and used: see Sec.2.5 for details and hints. In many cases, you
may simply edit file make.inc.

2.4.2    Environment variables
The behavior of configure can be changed by defining some environment variables. These can
be set in any of these ways:

        export VARIABLE=value; ./configure                      # sh, bash, ksh
        setenv VARIABLE value; ./configure                      # csh, tcsh
        env VARIABLE=value ./configure                          # any shell
        ./configure VARIABLE=value                              # any shell

Some environment variables that are relevant to configure are:
   ARCH                       label identifying the machine type (see next section)
   F90, CC                    names of Fortran and C compilers
   MPIF90                     name of parallel Fortran 90 compiler (using MPI)
   CPP                        source file preprocessor (defaults to $CC -E)
   LD                         linker (defaults to $MPIF90)
   (C,F,F90,CPP,LD)FLAGS compilation/preprocessor/loader flags
   LIBDIRS                    extra directories where to search for libraries
    IMPORTANT: as a rule, DO NOT DEFINE environment variables for configure, except
those needed to have your compiler and libraries working. Always try configure with no
further options as a first step, unless you have a good reason to specify them.

                                               10
```
