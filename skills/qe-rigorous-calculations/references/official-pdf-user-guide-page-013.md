# user_guide.pdf — page 13

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `8ee29226088b6c995921a986773ed57f5038cb8f30cfb6417b839dffc4ca27da`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 --with-cuda=value           enable compilation of GPU-accelerated subroutines.
                             value should point the path where the CUDA toolkit
                             is installed, e.g. $NVHPC CUDA HOME
 --with-cuda-cc=value        sets the compute capabilities for the compilation
                             of the accelerated subroutines.
                             value must be consistent with the hardware and the
                             NVidia driver installed on the workstation or on the
                             compute nodes of the HPC facility (default: 35)
 --with-cuda-runtime=value (optional) sets the version of the CUDA toolkit used
                             for the compilation of the accelerated code.
                             value must be consistent with the
                             CUDA Toolkit installed on the workstation
                             or available on the compute nodes of the HPC facility.
 --with-cuda-mpi=value       yes enables the usage of CUDA-aware MPI library.
                             Beware: if you have no fast inter-GPU communications, e.g.,
                             NVlink or Infiniband RDMA, you may get a crash at run time.
                             Important for optimal parallel performances (default: no).
 --enable-nvtx=value         enable NVTX profiling (for developers, default: no).
   To modify or extend configure (advanced users only!), see the Wiki pages on GitLab:
https://gitlab.com/QEF/q-e/-/wikis.

2.4.6   Manual configuration
If configure stops before the end, and you don’t find a way to fix it, you have to write a
working make.inc file (optionally, include/qe cdefs.h). The template used by configure
is install/make.inc.in and contains explanations of the meaning of the various variables.
Note that you may need to select appropriate preprocessing flags in conjunction with the
desired or available libraries (e.g. you need to add -D FFTW to DFLAGS if you want to link
internal FFTW). For a correct choice of preprocessing flags, refer to the documentation in
include/defs.h.README.
    Even if configure works, you may need to tweak the make.inc file. It is very simple, but
please note that a) you must know what you are doing, and b) if you change any settings (e.g.
preprocessing, compilation flags) after a previous, successful or failed, compilation, you must
run make clean before recompiling, unless you know exactly which routines are affected by
the changed settings and how to force their recompilation. Running configure again cleans
objects and executables, unless you use option --save.

2.5     Libraries
2.5.1   BLAS and LAPACK
Quantum ESPRESSO needs the BLAS and LAPACK mathematical libraries. As a rule,
one should always use vendor-specific optimized BLAS and LAPACK, such as e.g. those found
in Intel’s MKL. They often yield huge performance gains with respect to compiled libraries.
configure always try to locate the best mathematical libraries.
    If optimized BLAS and LAPACK are not available, Quantum ESPRESSO automatically
downloads and compiles them. Another option is to try the ATLAS library: http://math-atlas.source
Note that ATLAS is not a complete replacement for LAPACK: it contains all of the BLAS, plus

                                              13
```
