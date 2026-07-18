# CP2K official manual snapshot: global

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html
- Raw SHA-256: fd18212f47cd8857a993458fe152494e91ebba947f4017c2f6d27369416ae1e5
- Status: version-matched cached official text; reopen the source for current live verification.

GLOBAL



Section with general information on which kind of simulation to perform and parameters for the whole PROGRAM

[

Edit on GitHub

]

Subsections

DBCSR

FM

FM_DIAG_SETTINGS

GRID

PRINT

PROGRAM_RUN_INFO

REFERENCES

TIMINGS

Keywords



ALLTOALL_SGL

BLACS_GRID

BLACS_REPEATABLE

CALLGRAPH

CALLGRAPH_FILE_NAME

DIRECT_GENERALIZED_DIAGONALIZATION

DLAF_CHOLESKY_N_MIN

DLAF_NEIGVEC_MIN

ECHO_ALL_HOSTS

ECHO_INPUT

ELPA_KERNEL

ELPA_NEIGVEC_MIN

ELPA_ONE_STAGE

ELPA_PRINT

ELPA_QR

ENABLE_MPI_IO

EPS_CHECK_DIAG

EXTENDED_FFT_LENGTHS

FFTW_PLAN_TYPE

FFTW_WISDOM_FILE_NAME

FFT_POOL_SCRATCH_LIMIT

FLUSH_SHOULD_FLUSH

OUTPUT_FILE_NAME

PREFERRED_CHOLESKY_LIBRARY

PREFERRED_DGEMM_LIBRARY

PREFERRED_DIAG_LIBRARY

PREFERRED_FFT_LIBRARY

PRINT_LEVEL

PROGRAM_NAME

PROJECT_NAME

RUN_TYPE

SAVE_MEM

SEED

TRACE

TRACE_MASTER

TRACE_MAX

TRACE_ROUTINES

WALLTIME

Keyword descriptions



ALLTOALL_SGL

:

logical

=

F



Lone keyword:

T

Usage:

ALLTOALL_SGL YES

All-to-all communication (FFT) should use single precision

[

Edit on GitHub

]

BLACS_GRID

:

enum

=

SQUARE



Usage:

BLACS_GRID SQUARE

Valid values:

SQUARE

Distribution by matrix blocks

ROW

Distribution by matrix rows

COLUMN

Distribution by matrix columns

how to distribute the processors on the 2d grid needed by BLACS (and thus SCALAPACK)

[

Edit on GitHub

]

BLACS_REPEATABLE

:

logical

=

F



Lone keyword:

T

Usage:

BLACS_REPEATABLE

Use a topology for BLACS collectives that is guaranteed to be repeatable on homogeneous architectures

[

Edit on GitHub

]

CALLGRAPH

:

enum

=

NONE



Lone keyword:

MASTER

Usage:

CALLGRAPH {NONE|MASTER|ALL}

Valid values:

NONE

No callgraph gets written

MASTER

Only the master process writes his callgraph

ALL

All processes write their callgraph (into a separate files).

At the end of the run write a callgraph to file, which contains detailed timing informations. This callgraph can be viewed e.g. with the open-source program kcachegrind.

[

Edit on GitHub

]

CALLGRAPH_FILE_NAME

:

string



Usage:

CALLGRAPH_FILE_NAME {filename}

Name of the callgraph file, which is written at the end of the run. If not specified the project name will be used as filename.

[

Edit on GitHub

]

DIRECT_GENERALIZED_DIAGONALIZATION

:

logical

=

F



Lone keyword:

T

Usage:

DIRECT_GENERALIZED_DIAGONALIZATION

Request direct generalized eigenvalue problem diagonalization without a CP2K-side Cholesky reduction in supported dense matrix paths. The eigensolver is still selected by PREFERRED_DIAG_LIBRARY.

[

Edit on GitHub

]

DLAF_CHOLESKY_N_MIN

:

integer

=

1024



Usage:

DLAF_CHOLESKY_N_MIN 512

Mentions:

⭐

DLA-Future

Minimum matrix size for the use of the Cholesky decomposition from the DLA-Future library. The Cholesky decomposition from the ScaLAPACK library is used as fallback for all smaller cases

[

Edit on GitHub

]

DLAF_NEIGVEC_MIN

:

integer

=

1024



Usage:

DLAF_NEIGVEC_MIN 512

Mentions:

⭐

DLA-Future

Minimum number of eigenvectors for the use of the eigensolver from the DLA-Future library. The eigensolver from the ScaLAPACK library is used as fallback for all smaller cases

[

Edit on GitHub

]

ECHO_ALL_HOSTS

:

logical

=

F



Lone keyword:

T

Usage:

ECHO_ALL_HOSTS NO

Echo a list of hostname and pid for all MPI processes.

[

Edit on GitHub

]

ECHO_INPUT

:

logical

=

F



Lone keyword:

T

Usage:

ECHO_INPUT NO

If the input should be echoed to the output with all the defaults made explicit

[

Edit on GitHub

]

ELPA_KERNEL

:

enum

=

AUTO



Valid values:

AUTO

Automatically selected kernel

GENERIC

Generic kernel

GENERIC_SIMPLE

Simplified generic kernel

BGP

Kernel optimized for IBM BGP

BGQ

Kernel optimized for IBM BGQ

SSE

Kernel optimized for x86_64/SSE

SSE_BLOCK2

Kernel optimized for x86_64/SSE (block=2)

SSE_BLOCK4

Kernel optimized for x86_64/SSE (block=4)

SSE_BLOCK6

Kernel optimized for x86_64/SSE (block=6)

AVX_BLOCK2

Kernel optimized for Intel AVX (block=2)

AVX_BLOCK4

Kernel optimized for Intel AVX (block=4)

AVX_BLOCK6

Kernel optimized for Intel AVX (block=6)

AVX2_BLOCK2

Kernel optimized for Intel AVX2 (block=2)

AVX2_BLOCK4

Kernel optimized for Intel AVX2 (block=4)

AVX2_BLOCK6

Kernel optimized for Intel AVX2 (block=6)

AVX512_BLOCK2

Kernel optimized for Intel AVX-512 (block=2)

AVX512_BLOCK4

Kernel optimized for Intel AVX-512 (block=4)

AVX512_BLOCK6

Kernel optimized for Intel AVX-512 (block=6)

NVIDIA_GPU

Kernel targeting Nvidia GPUs

AMD_GPU

Kernel targeting AMD GPUs

INTEL_GPU

Kernel targeting Intel GPUs

Specifies the kernel to be used when ELPA is in use

[

Edit on GitHub

]

ELPA_NEIGVEC_MIN

:

integer

=

64



Usage:

ELPA_NEIGVEC_MIN 32

Minimum number of eigenvectors for the use of the eigensolver from the ELPA library. The eigensolver from the ScaLAPACK library is used as fallback for all smaller cases

[

Edit on GitHub

]

ELPA_ONE_STAGE

:

logical

=

F



Lone keyword:

T

Usage:

ELPA_ONE_STAGE

For ELPA, enable the one-stage solver (instead of the two-stage solver). Please note, ELPA_QR and ELPA_KERNEL settings may be ignored.

[

Edit on GitHub

]

ELPA_PRINT

:

logical

=

F



Lone keyword:

T

Usage:

ELPA_PRINT

Controls the printing of ELPA diagonalization information. Useful for testing purposes, especially together with keyword ELPA_QR.

[

Edit on GitHub

]

ELPA_QR

:

logical

=

F



Lone keyword:

T

Usage:

ELPA_QR

For ELPA, enable a blocked QR step when reducing the input matrix to banded form before diagonalization. Requires ELPA version 201505 or newer and is automatically deactivated otherwise. QR is activated only when the matrix size is suitable. Keyword ELPA_PRINT helps identify suitable cases. Can accelerate diagonalization for suitable matrices.

[

Edit on GitHub

]

ENABLE_MPI_IO

:

logical

=

T



Lone keyword:

T

Usage:

ENABLE_MPI_IO FALSE

Enable MPI parallelization for all supported I/O routines Currently, only cube file writer/reader routines use MPI I/O. Disabling this flag might speed up calculations dominated by I/O.

[

Edit on GitHub

]

EPS_CHECK_DIAG

:

real

=

-1.00000000E+000



Usage:

EPS_CHECK_DIAG 1.0E-14

Check that the orthonormality of the eigenvectors after a diagonalization fulfills the specified numerical accuracy. A negative threshold value disables the check.

[

Edit on GitHub

]

EXTENDED_FFT_LENGTHS

:

logical

=

F



Lone keyword:

T

Usage:

EXTENDED_FFT_LENGTHS

Mentions:

⭐

Troubleshooting

Use fft library specific values for the allows number of points in FFTs. The default is to use the internal FFT lengths. For external fft libraries this may create an error at the external library level, because the length provided by cp2k is not supported by the external library. In this case switch on this keyword to obtain, with certain fft libraries, lengths matching the external fft library lengths, or larger allowed grids, or grids that more precisely match a given cutoff. IMPORTANT NOTE: in this case, the actual grids used in CP2K depends on the FFT library. A change of FFT library must therefore be considered equivalent to a change of basis, which implies a change of total energy.

[

Edit on GitHub

]

FFTW_PLAN_TYPE

:

enum

=

ESTIMATE



Usage:

FFTW_PLAN_TYPE PATIENT

Valid values:

ESTIMATE

Quick estimate, no runtime measurements.

MEASURE

Quick measurement, somewhat faster FFTs.

PATIENT

Measurements trying a wider range of possibilities.

EXHAUSTIVE

Measurements trying all possibilities - use with caution.

References:

Frigo2005

FFTW can have improved performance if it is allowed to plan with explicit measurements which strategy is best for a given FFT. While a plan based on measurements is generally faster, differences in machine load will lead to different plans for the same input file, and thus numerics for the FFTs will be slightly different from run to run. PATIENT planning is recommended for long ab initio MD runs.

[

Edit on GitHub

]

FFTW_WISDOM_FILE_NAME

:

string

=

/etc/fftw/wisdom



Usage:

FFTW_WISDOM_FILE_NAME wisdom.dat

The name of the file that contains wisdom (pre-planned FFTs) for use with FFTW3. Using wisdom can significantly speed up the FFTs (see the FFTW homepage for details). Note that wisdom is not transferable between different computer (architectures). Wisdom can be generated using the fftw-wisdom tool that is part of the fftw installation. cp2k/tools/cp2k-wisdom is a script that contains some additional info, and can help to generate a useful default for /etc/fftw/wisdom or particular values for a given simulation.

[

Edit on GitHub

]

FFT_POOL_SCRATCH_LIMIT

:

integer

=

15



Usage:

FFT_POOL_SCRATCH_LIMIT {INTEGER}

Limits the memory usage of the FFT scratch pool, potentially reducing efficiency a bit

[

Edit on GitHub

]

FLUSH_SHOULD_FLUSH

:

logical

=

T



Lone keyword:

T

Usage:

FLUSH_SHOULD_FLUSH

Flush output regularly, enabling this option might degrade performance significantly on certain machines.

[

Edit on GitHub

]

OUTPUT_FILE_NAME

:

string



Usage:

OUTPUT_FILE_NAME {filename}

Name of the output file. Relevant only if automatically started (through farming for example). If empty uses the project name as basis for it.

[

Edit on GitHub

]

PREFERRED_CHOLESKY_LIBRARY

:

enum

=

SCALAPACK



Usage:

PREFERRED_CHOLESKY_LIBRARY DLAF

Valid values:

SCALAPACK

ScaLAPACK library

SL

ScaLAPACK library (shorthand)

DLAF

DLA-Future (CUDA/HIP GPU library)

Mentions:

⭐

DLA-Future

Specifies Cholesky decomposition library to be used. If not available, the ScaLAPACK library is used

[

Edit on GitHub

]

PREFERRED_DGEMM_LIBRARY

:

enum

=

BLAS



Usage:

PREFERRED_DGEMM_LIBRARY SPLA

Valid values:

SPLA

SPLA library

BLAS

BLAS library

Specifies the DGEMM library to be used. If not available, the BLAS routine is used. This keyword affects some DGEMM calls in the WFC code and turns on their acceleration with SpLA. This keyword affects only local DGEMM calls, not the calls to PDGEMM (see keyword FM%TYPE_OF_MATRIX_MULTIPLICATION).

[

Edit on GitHub

]

PREFERRED_DIAG_LIBRARY

:

enum

=

ELPA



Usage:

PREFERRED_DIAG_LIBRARY ELPA

Valid values:

ELPA

ELPA library

SCALAPACK

ScaLAPACK library

SL

ScaLAPACK library (shorthand)

CUSOLVER

cuSOLVER (CUDA GPU library)

DLAF

DLA-Future (CUDA/HIP GPU library)

Mentions:

⭐

Troubleshooting

, ⭐

DLA-Future

Specifies the diagonalization library to be used. If not available, the ScaLAPACK library is used

[

Edit on GitHub

]

PREFERRED_FFT_LIBRARY

:

enum

=

FFTW3



Usage:

PREFERRED_FFT_LIBRARY FFTW3

Valid values:

FFTSG

Stefan Goedecker’s FFT (FFTSG), always available, will be used in case a FFT library is specified and not available.

FFTW3

a fast portable FFT library. Recommended. See also the FFTW_PLAN_TYPE, and FFTW_WISDOM_FILE_NAME keywords.

FFTW

Same as FFTW3 (for compatibility with CP2K 2.3)

References:

Frigo2005

Mentions:

⭐

Troubleshooting

Specifies the FFT library which should be preferred. If it is not available, use FFTW3 if this is linked in, if FFTW3 is not available use FFTSG. Improved performance with FFTW3 can be obtained specifying a proper value for FFTW_PLAN_TYPE. Contrary to earlier CP2K versions, all libraries will result in the same grids, i.e. the subset of grids which all FFT libraries can transform. See EXTENDED_FFT_LENGTHS if larger FFTs or grids that more precisely match a given cutoff are needed, or older results need to be reproduced. FFTW3 is often (close to) optimal, and well tested with CP2K.

[

Edit on GitHub

]

PRINT_LEVEL

:

enum

=

MEDIUM



Aliases:

IOLEVEL

Usage:

PRINT_LEVEL HIGH

Valid values:

SILENT

Almost no output

LOW

Little output

MEDIUM

Quite some output

HIGH

Lots of output

DEBUG

Everything is written out, useful for debugging purposes only

Mentions:

⭐

How to Converge the CUTOFF and REL_CUTOFF

, ⭐

HFX-RI with k-Points

How much output is written out.

[

Edit on GitHub

]

PROGRAM_NAME

:

enum

=

CP2K



Aliases:

PROGRAM

Usage:

PROGRAM_NAME {STRING}

Valid values:

ATOM

Runs single atom calculations

FARMING

Runs N independent jobs in a single run

TEST

Do some benchmarking and testing

CP2K

Runs one of the CP2K package

OPTIMIZE_INPUT

A tool to optimize parameters in a CP2K input

OPTIMIZE_BASIS

A tool to create a MOLOPT or ADMM basis for a given set of training structures

TMC

Runs Tree Monte Carlo algorithm using additional input file(s)

MC_ANALYSIS

Runs (Tree) Monte Carlo trajectory file analysis

SWARM

Runs swarm based calculation

Which program should be run

[

Edit on GitHub

]

PROJECT_NAME

:

string

=

PROJECT



Aliases:

PROJECT

Usage:

PROJECT_NAME {STRING}

Mentions:

⭐

Molecular Dynamics

Name of the project (used to build the name of the trajectory, and other files generated by the program)

[

Edit on GitHub

]

RUN_TYPE

:

enum

=

ENERGY_FORCE



Usage:

RUN_TYPE MD

Valid values:

NONE

Perform no tasks

ENERGY

Computes energy

ENERGY_FORCE

Computes energy and forces

MD

Molecular Dynamics

GEO_OPT

Geometry Optimization

MC

Monte Carlo

DEBUG

Performs a Debug analysis

BSSE

Basis set superposition error

LR

Linear Response

PINT

Path integral

VIBRATIONAL_ANALYSIS

Vibrational analysis

BAND

Band methods

CELL_OPT

Cell optimization. Both cell vectors and atomic positions are optimised.

WFN_OPT

Alias for ENERGY

WAVEFUNCTION_OPTIMIZATION

Alias for ENERGY

MOLECULAR_DYNAMICS

Alias for MD

GEOMETRY_OPTIMIZATION

Alias for GEO_OPT

MONTECARLO

Alias for MC

LINEAR_RESPONSE

Alias for LR

NORMAL_MODES

Alias for VIBRATIONAL_ANALYSIS

RT_PROPAGATION

Real Time propagation run (fixed ionic positions)

EHRENFEST_DYN

Ehrenfest dynamics (using real time propagation of the wavefunction)

TAMC

Temperature Accelerated Monte Carlo (TAMC)

TMC

Tree Monte Carlo (TMC), a pre-sampling MC algorithm

DRIVER

i-PI driver mode

NEGF

Non-equilibrium Green’s function method

MIMIC

Run as a client in a simulation through the MiMiC framework

RTP

Alias for RT_PROPAGATION

References:

Ceriotti2014

,

Schonherr2014

Mentions:

⭐

Run a First Calculation

, ⭐

How to Converge the CUTOFF and REL_CUTOFF

, ⭐

Band structure from GW

, ⭐

Geometry and cell optimization

, ⭐

GW + Bethe-Salpeter equation

, ⭐

Time-Dependent DFT

, ⭐

Simulating Vibronic Effects in Optical Spectra

, ⭐

X-Ray Absorption from TDDFT

, ⭐

Real-Time Propagation and Ehrenfest MD

, ⭐

Molecular Dynamics

, ⭐

Monte Carlo

Selects the top-level task CP2K should run, such as an energy, energy-and-force, molecular dynamics, geometry optimization, or response calculation.

[

Edit on GitHub

]

SAVE_MEM

:

logical

=

F



Lone keyword:

T

Usage:

SAVE_MEM

Some sections of the input structure are deallocated when not needed, and reallocated only when used. This reduces the required maximum memory.

[

Edit on GitHub

]

SEED

:

integer[

]

=

2000



Usage:

SEED {INTEGER} .. {INTEGER}

Initial seed for the global (pseudo)random number generator to create a stream of normally Gaussian distributed random numbers. Exactly 1 or 6 positive integer values are expected. A single value is replicated to fill up the full seed array with 6 numbers.

[

Edit on GitHub

]

TRACE

:

logical

=

F



Lone keyword:

T

Usage:

TRACE

If a debug trace of the execution of the program should be written

[

Edit on GitHub

]

TRACE_MASTER

:

logical

=

T



Lone keyword:

T

Usage:

TRACE_MASTER

For parallel TRACEd runs: only the master node writes output.

[

Edit on GitHub

]

TRACE_MAX

:

integer

=

2147483647



Usage:

TRACE_MAX 100

Limit the total number a given subroutine is printed in the trace. Accounting is not influenced.

[

Edit on GitHub

]

TRACE_ROUTINES

:

string[

]



Usage:

TRACE_ROUTINES {routine_name1} {routine_name2} …

A list of routines to trace. If left empty all routines are traced. Accounting is not influenced.

[

Edit on GitHub

]

WALLTIME

:

string



Aliases:

WALLTI

Usage:

WALLTIME {real} or {HH:MM:SS}

Mentions:

⭐

Geometry and cell optimization

Maximum execution time for this run. Time in seconds or in HH:MM:SS.

[

Edit on GitHub

]
