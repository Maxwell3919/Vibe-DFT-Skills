# user_guide.pdf — page 23

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `05d50893e5215c7dd8bf4fb91f5a3e11a3fa35e77dda6642fe20c9521d9102a1`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
which gives an additional 10-20% speedup with MKL 2020, while for earlier versions the speedup
is greater than 200%. [...] Another note, there seem to be problems using FFTW interface of
MKL with AMD cpus. To get around this problem, one has to additionally set
export MKL_CBWR=AUTO
“ (Info by Tobias Klöffel, Feb. 2020)

2.9.3   Linux PC clusters with MPI
PC clusters running some version of MPI are a very popular computational platform nowadays.
Quantum ESPRESSO is known to work with at least the MPICH2 and OpenMPI implemen-
tations. configure should automatically recognize a properly installed parallel environment
and prepare for parallel compilation. Unfortunately this not always happens. In fact:
   • configure tries to locate a parallel compiler in a logical place with a logical name, but
     if it has a strange names or it is located in a strange location, you will have to instruct
     configure to find it. If there is no parallel Fortran compiler (e.g., mpif90), you will have
     to install one.

   • configure tries to locate libraries (both mathematical and parallel libraries) in the usual
     places with usual names, but if they have strange names or strange locations, you will
     have to rename/move them, or to instruct configure to find them. If MPI libraries are
     not found, parallel compilation is disabled.

   • configure tests that the compiler and the libraries are compatible (i.e. the compiler may
     link the libraries without conflicts and without missing symbols). If they aren’t and the
     compilation fails, configure will revert to serial compilation.
    Apart from such problems, Quantum ESPRESSO compiles and works on all non-buggy,
properly configured hardware and software combinations. In some cases you may have to
recompile MPI libraries: not all MPI installations contain support for the Fortran compiler of
your choice (or for any Fortran compiler at all).
    If Quantum ESPRESSO does not work for some reason on a PC cluster, try first if
it works in serial execution. A frequent problem with parallel execution is that Quantum
ESPRESSO does not read from standard input, due to the configuration of MPI libraries: see
Sec.3.5. If you are dissatisfied with the performances in parallel execution, see Sec.3 and in
particular Sec.3.5.

2.9.4   Microsoft Windows
Currently the safest way to build Quantum ESPRESSO on Windows is to enable the
Windows Subsystem for Linux (WSL) v.2, available on Windows 10 and 11. You may in-
stall a Linux distribution you like and compile as on Linux. It works very well. See here:
https://learn.microsoft.com/en-us/windows/wsl/install
    Another option is Quantum Mobile: https://www.materialscloud.org/work/quantum-mobile.
    If you prefere a native Windows build, you are welcome to try the various possibilities listed
below and to report details in case of success.
    Since February 2020 Quantum ESPRESSO can be compiled on MS-Windows 10 using
PGI 19.10 Community Edition (freely downloadable). configure works with the bash script

                                               23
```
