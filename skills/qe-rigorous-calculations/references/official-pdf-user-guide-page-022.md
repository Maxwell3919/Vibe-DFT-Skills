# user_guide.pdf — page 22

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `4e8e8e5696b4efa93d061bed0c0fcf4bd24b6483e891eb70d22b76b271904d3d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2.9.2   Linux PC’s
Both AMD and Intel CPUs, 32-bit and 64-bit, are supported and work, either in 32-bit emu-
lation and in 64-bit mode. 64-bit executables can address a much larger memory space than
32-bit executable, but there is no gain in speed. Beware: the default integer type for 64-bit
machine is typically 32-bit long. You should be able to use 64-bit integers as well, but it is not
guaranteed to work and will not give any advantage anyway.
    It is usually convenient to create semi-statically linked executables (with only libc, libm,
libpthread dynamically linked). If you want to produce a binary that runs on different machines,
compile it on the oldest machine you have (i.e. the one with the oldest version of the operating
system).
    Currently, configure supports, and Quantum ESPRESSO works with, not-too-old and
not-too-buggy versions of gfortran, Intel (ifx, ifort), NVidia (nvfortran), AMD (AOCC v.5),
ARM (armflang), Cray (ftn) compilers.

Linux PCs with Intel compiler (ifx, ifort) If configure doesn’t find the compiler, or
if you get Error loading shared libraries at run time, you may have forgotten to execute the
script that sets up the correct PATH and library path. Unless your system manager has done
this for you, you should execute the appropriate script – located in the directory containing the
compiler executable – in your initialization files. Consult the documentation provided by Intel.

Linux PCs with MKL libraries On Intel CPUs it is very convenient to use Intel MKL
libraries (freely available together with the Intel compiler at https://software.intel.com).
They can be used also with non-Intel compilers. With gfortran, one has to link -lmkl gf lp64
instead of -lmkl intel lp64 (configure should take care of it).
    configure properly detects MKL libraries, as long as the $MKLROOT environment vari-
able is set in the current shell. Normally this environment variable is set by sourcing the
environment script provided by Intel.
    By default the non-threaded version of MKL is linked, unless option configure --with-openmp
is specified. In case of trouble, refer to the following web page to find the correct way to link
MKL:
http://software.intel.com/en-us/articles/intel-mkl-link-line-advisor/.
    For parallel (MPI) execution on multiprocessor (SMP) machines, set the environment vari-
able OMP NUM THREADS to 1 unless you know how to run MPI+OpenMP. See Sec.3 for
more info on this and on the difference between MPI and OpenMP parallelization.

Linux PCs with AMD processors For AMD CPUs there are optimized libraries called
AOCL, AMD Optimizing CPU Libraries, bundled with the AOCC v.5 compiler, freely available
from AMD.
   “ Recently I played around with some AMD EPYC cpus and the bad thing is that I also
saw some strange numbers when using libflame/aocl 2.1. (...) Since version 2020 the MKL
performs rather well when using AMD cpus, however, if you want to get the best performance
you have to additionally set:

export MKL_DEBUG_CPU_TYPE=5




                                               22
```
