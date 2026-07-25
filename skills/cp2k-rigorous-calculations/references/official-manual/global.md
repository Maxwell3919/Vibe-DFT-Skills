# CP2K official manual snapshot: global

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html
- Raw SHA-256: fd18212f47cd8857a993458fe152494e91ebba947f4017c2f6d27369416ae1e5
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# GLOBAL

Section with general information on which kind of simulation to perform and parameters for the whole PROGRAM \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L100)\]

Subsections

-   [DBCSR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/DBCSR.html)
-   [FM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/FM.html)
-   [FM\_DIAG\_SETTINGS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/FM_DIAG_SETTINGS.html)
-   [GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/GRID.html)
-   [PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PRINT.html)
-   [PROGRAM\_RUN\_INFO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/PROGRAM_RUN_INFO.html)
-   [REFERENCES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/REFERENCES.html)
-   [TIMINGS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL/TIMINGS.html)

## Keywords

-   [ALLTOALL\_SGL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ALLTOALL_SGL "CP2K_INPUT.GLOBAL.ALLTOALL_SGL")

-   [BLACS\_GRID](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.BLACS_GRID "CP2K_INPUT.GLOBAL.BLACS_GRID")

-   [BLACS\_REPEATABLE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.BLACS_REPEATABLE "CP2K_INPUT.GLOBAL.BLACS_REPEATABLE")

-   [CALLGRAPH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.CALLGRAPH "CP2K_INPUT.GLOBAL.CALLGRAPH")

-   [CALLGRAPH\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.CALLGRAPH_FILE_NAME "CP2K_INPUT.GLOBAL.CALLGRAPH_FILE_NAME")

-   [DIRECT\_GENERALIZED\_DIAGONALIZATION](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.DIRECT_GENERALIZED_DIAGONALIZATION "CP2K_INPUT.GLOBAL.DIRECT_GENERALIZED_DIAGONALIZATION")

-   **[DLAF\_CHOLESKY\_N\_MIN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.DLAF_CHOLESKY_N_MIN "CP2K_INPUT.GLOBAL.DLAF_CHOLESKY_N_MIN")**

-   **[DLAF\_NEIGVEC\_MIN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.DLAF_NEIGVEC_MIN "CP2K_INPUT.GLOBAL.DLAF_NEIGVEC_MIN")**

-   [ECHO\_ALL\_HOSTS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ECHO_ALL_HOSTS "CP2K_INPUT.GLOBAL.ECHO_ALL_HOSTS")

-   [ECHO\_INPUT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ECHO_INPUT "CP2K_INPUT.GLOBAL.ECHO_INPUT")

-   [ELPA\_KERNEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ELPA_KERNEL "CP2K_INPUT.GLOBAL.ELPA_KERNEL")

-   [ELPA\_NEIGVEC\_MIN](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ELPA_NEIGVEC_MIN "CP2K_INPUT.GLOBAL.ELPA_NEIGVEC_MIN")

-   [ELPA\_ONE\_STAGE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ELPA_ONE_STAGE "CP2K_INPUT.GLOBAL.ELPA_ONE_STAGE")

-   [ELPA\_PRINT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ELPA_PRINT "CP2K_INPUT.GLOBAL.ELPA_PRINT")

-   [ELPA\_QR](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ELPA_QR "CP2K_INPUT.GLOBAL.ELPA_QR")

-   [ENABLE\_MPI\_IO](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.ENABLE_MPI_IO "CP2K_INPUT.GLOBAL.ENABLE_MPI_IO")

-   [EPS\_CHECK\_DIAG](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.EPS_CHECK_DIAG "CP2K_INPUT.GLOBAL.EPS_CHECK_DIAG")

-   **[EXTENDED\_FFT\_LENGTHS](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.EXTENDED_FFT_LENGTHS "CP2K_INPUT.GLOBAL.EXTENDED_FFT_LENGTHS")**

-   [FFTW\_PLAN\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.FFTW_PLAN_TYPE "CP2K_INPUT.GLOBAL.FFTW_PLAN_TYPE")

-   [FFTW\_WISDOM\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.FFTW_WISDOM_FILE_NAME "CP2K_INPUT.GLOBAL.FFTW_WISDOM_FILE_NAME")

-   [FFT\_POOL\_SCRATCH\_LIMIT](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.FFT_POOL_SCRATCH_LIMIT "CP2K_INPUT.GLOBAL.FFT_POOL_SCRATCH_LIMIT")

-   [FLUSH\_SHOULD\_FLUSH](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.FLUSH_SHOULD_FLUSH "CP2K_INPUT.GLOBAL.FLUSH_SHOULD_FLUSH")

-   [OUTPUT\_FILE\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.OUTPUT_FILE_NAME "CP2K_INPUT.GLOBAL.OUTPUT_FILE_NAME")

-   **[PREFERRED\_CHOLESKY\_LIBRARY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PREFERRED_CHOLESKY_LIBRARY "CP2K_INPUT.GLOBAL.PREFERRED_CHOLESKY_LIBRARY")**

-   [PREFERRED\_DGEMM\_LIBRARY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PREFERRED_DGEMM_LIBRARY "CP2K_INPUT.GLOBAL.PREFERRED_DGEMM_LIBRARY")

-   **[PREFERRED\_DIAG\_LIBRARY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PREFERRED_DIAG_LIBRARY "CP2K_INPUT.GLOBAL.PREFERRED_DIAG_LIBRARY")**

-   **[PREFERRED\_FFT\_LIBRARY](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PREFERRED_FFT_LIBRARY "CP2K_INPUT.GLOBAL.PREFERRED_FFT_LIBRARY")**

-   **[PRINT\_LEVEL](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PRINT_LEVEL "CP2K_INPUT.GLOBAL.PRINT_LEVEL")**

-   [PROGRAM\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PROGRAM_NAME "CP2K_INPUT.GLOBAL.PROGRAM_NAME")

-   **[PROJECT\_NAME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.PROJECT_NAME "CP2K_INPUT.GLOBAL.PROJECT_NAME")**

-   **[RUN\_TYPE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.RUN_TYPE "CP2K_INPUT.GLOBAL.RUN_TYPE")**

-   [SAVE\_MEM](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.SAVE_MEM "CP2K_INPUT.GLOBAL.SAVE_MEM")

-   [SEED](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.SEED "CP2K_INPUT.GLOBAL.SEED")

-   [TRACE](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.TRACE "CP2K_INPUT.GLOBAL.TRACE")

-   [TRACE\_MASTER](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.TRACE_MASTER "CP2K_INPUT.GLOBAL.TRACE_MASTER")

-   [TRACE\_MAX](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.TRACE_MAX "CP2K_INPUT.GLOBAL.TRACE_MAX")

-   [TRACE\_ROUTINES](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.TRACE_ROUTINES "CP2K_INPUT.GLOBAL.TRACE_ROUTINES")

-   **[WALLTIME](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/GLOBAL.html#CP2K_INPUT.GLOBAL.WALLTIME "CP2K_INPUT.GLOBAL.WALLTIME")**


## Keyword descriptions

### ALLTOALL\_SGL*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ALLTOALL\_SGL YES*

All-to-all communication (FFT) should use single precision \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L332)\]

### BLACS\_GRID*: enum* *\= SQUARE*

**Usage:** *BLACS\_GRID SQUARE*

**Valid values:**

-   `SQUARE` Distribution by matrix blocks

-   `ROW` Distribution by matrix rows

-   `COLUMN` Distribution by matrix columns


how to distribute the processors on the 2d grid needed by BLACS (and thus SCALAPACK) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L106)\]

### BLACS\_REPEATABLE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *BLACS\_REPEATABLE*

Use a topology for BLACS collectives that is guaranteed to be repeatable on homogeneous architectures \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L116)\]

### CALLGRAPH*: enum* *\= NONE*

**Lone keyword:** `MASTER`

**Usage:** *CALLGRAPH {NONE|MASTER|ALL}*

**Valid values:**

-   `NONE` No callgraph gets written

-   `MASTER` Only the master process writes his callgraph

-   `ALL` All processes write their callgraph (into a separate files).


At the end of the run write a callgraph to file, which contains detailed timing informations. This callgraph can be viewed e.g. with the open-source program kcachegrind. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L495)\]

### CALLGRAPH\_FILE\_NAME*: string*

**Usage:** *CALLGRAPH\_FILE\_NAME {filename}*

Name of the callgraph file, which is written at the end of the run. If not specified the project name will be used as filename. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L509)\]

### DIRECT\_GENERALIZED\_DIAGONALIZATION*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *DIRECT\_GENERALIZED\_DIAGONALIZATION*

Request direct generalized eigenvalue problem diagonalization without a CP2K-side Cholesky reduction in supported dense matrix paths. The eigensolver is still selected by PREFERRED\_DIAG\_LIBRARY. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L143)\]

### DLAF\_CHOLESKY\_N\_MIN*: integer* *\= 1024*

**Usage:** *DLAF\_CHOLESKY\_N\_MIN 512*

**Mentions:** ⭐[DLA-Future](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/dlaf.html)

Minimum matrix size for the use of the Cholesky decomposition from the DLA-Future library. The Cholesky decomposition from the ScaLAPACK library is used as fallback for all smaller cases \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L246)\]

### DLAF\_NEIGVEC\_MIN*: integer* *\= 1024*

**Usage:** *DLAF\_NEIGVEC\_MIN 512*

**Mentions:** ⭐[DLA-Future](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/dlaf.html)

Minimum number of eigenvectors for the use of the eigensolver from the DLA-Future library. The eigensolver from the ScaLAPACK library is used as fallback for all smaller cases \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L237)\]

### ECHO\_ALL\_HOSTS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ECHO\_ALL\_HOSTS NO*

Echo a list of hostname and pid for all MPI processes. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L444)\]

### ECHO\_INPUT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ECHO\_INPUT NO*

If the input should be echoed to the output with all the defaults made explicit \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L437)\]

### ELPA\_KERNEL*: enum* *\= AUTO*

**Valid values:**

-   `AUTO` Automatically selected kernel

-   `GENERIC` Generic kernel

-   `GENERIC_SIMPLE` Simplified generic kernel

-   `BGP` Kernel optimized for IBM BGP

-   `BGQ` Kernel optimized for IBM BGQ

-   `SSE` Kernel optimized for x86\_64/SSE

-   `SSE_BLOCK2` Kernel optimized for x86\_64/SSE (block=2)

-   `SSE_BLOCK4` Kernel optimized for x86\_64/SSE (block=4)

-   `SSE_BLOCK6` Kernel optimized for x86\_64/SSE (block=6)

-   `AVX_BLOCK2` Kernel optimized for Intel AVX (block=2)

-   `AVX_BLOCK4` Kernel optimized for Intel AVX (block=4)

-   `AVX_BLOCK6` Kernel optimized for Intel AVX (block=6)

-   `AVX2_BLOCK2` Kernel optimized for Intel AVX2 (block=2)

-   `AVX2_BLOCK4` Kernel optimized for Intel AVX2 (block=4)

-   `AVX2_BLOCK6` Kernel optimized for Intel AVX2 (block=6)

-   `AVX512_BLOCK2` Kernel optimized for Intel AVX-512 (block=2)

-   `AVX512_BLOCK4` Kernel optimized for Intel AVX-512 (block=4)

-   `AVX512_BLOCK6` Kernel optimized for Intel AVX-512 (block=6)

-   `NVIDIA_GPU` Kernel targeting Nvidia GPUs

-   `AMD_GPU` Kernel targeting AMD GPUs

-   `INTEL_GPU` Kernel targeting Intel GPUs


Specifies the kernel to be used when ELPA is in use \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L193)\]

### ELPA\_NEIGVEC\_MIN*: integer* *\= 64*

**Usage:** *ELPA\_NEIGVEC\_MIN 32*

Minimum number of eigenvectors for the use of the eigensolver from the ELPA library. The eigensolver from the ScaLAPACK library is used as fallback for all smaller cases \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L202)\]

### ELPA\_ONE\_STAGE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ELPA\_ONE\_STAGE*

For ELPA, enable the one-stage solver (instead of the two-stage solver). Please note, ELPA\_QR and ELPA\_KERNEL settings may be ignored. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L222)\]

### ELPA\_PRINT*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ELPA\_PRINT*

Controls the printing of ELPA diagonalization information. Useful for testing purposes, especially together with keyword ELPA\_QR. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L230)\]

### ELPA\_QR*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *ELPA\_QR*

For ELPA, enable a blocked QR step when reducing the input matrix to banded form before diagonalization. Requires ELPA version 201505 or newer and is automatically deactivated otherwise. QR is activated only when the matrix size is suitable. Keyword ELPA\_PRINT helps identify suitable cases. Can accelerate diagonalization for suitable matrices. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L211)\]

### ENABLE\_MPI\_IO*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *ENABLE\_MPI\_IO FALSE*

Enable MPI parallelization for all supported I/O routines Currently, only cube file writer/reader routines use MPI I/O. Disabling this flag might speed up calculations dominated by I/O. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L450)\]

### EPS\_CHECK\_DIAG*: real* *\= \-1.00000000E+000*

**Usage:** *EPS\_CHECK\_DIAG 1.0E-14*

Check that the orthonormality of the eigenvectors after a diagonalization fulfills the specified numerical accuracy. A negative threshold value disables the check. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L185)\]

### EXTENDED\_FFT\_LENGTHS*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *EXTENDED\_FFT\_LENGTHS*

**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html)

Use fft library specific values for the allows number of points in FFTs. The default is to use the internal FFT lengths. For external fft libraries this may create an error at the external library level, because the length provided by cp2k is not supported by the external library. In this case switch on this keyword to obtain, with certain fft libraries, lengths matching the external fft library lengths, or larger allowed grids, or grids that more precisely match a given cutoff. IMPORTANT NOTE: in this case, the actual grids used in CP2K depends on the FFT library. A change of FFT library must therefore be considered equivalent to a change of basis, which implies a change of total energy. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L311)\]

### FFTW\_PLAN\_TYPE*: enum* *\= ESTIMATE*

**Usage:** *FFTW\_PLAN\_TYPE PATIENT*

**Valid values:**

-   `ESTIMATE` Quick estimate, no runtime measurements.

-   `MEASURE` Quick measurement, somewhat faster FFTs.

-   `PATIENT` Measurements trying a wider range of possibilities.

-   `EXHAUSTIVE` Measurements trying all possibilities - use with caution.


**References:** [Frigo2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#frigo2005)

FFTW can have improved performance if it is allowed to plan with explicit measurements which strategy is best for a given FFT. While a plan based on measurements is generally faster, differences in machine load will lead to different plans for the same input file, and thus numerics for the FFTs will be slightly different from run to run. PATIENT planning is recommended for long ab initio MD runs. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L289)\]

### FFTW\_WISDOM\_FILE\_NAME*: string* *\= /etc/fftw/wisdom*

**Usage:** *FFTW\_WISDOM\_FILE\_NAME wisdom.dat*

The name of the file that contains wisdom (pre-planned FFTs) for use with FFTW3. Using wisdom can significantly speed up the FFTs (see the FFTW homepage for details). Note that wisdom is not transferable between different computer (architectures). Wisdom can be generated using the fftw-wisdom tool that is part of the fftw installation. cp2k/tools/cp2k-wisdom is a script that contains some additional info, and can help to generate a useful default for /etc/fftw/wisdom or particular values for a given simulation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L278)\]

### FFT\_POOL\_SCRATCH\_LIMIT*: integer* *\= 15*

**Usage:** *FFT\_POOL\_SCRATCH\_LIMIT {INTEGER}*

Limits the memory usage of the FFT scratch pool, potentially reducing efficiency a bit \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L326)\]

### FLUSH\_SHOULD\_FLUSH*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *FLUSH\_SHOULD\_FLUSH*

Flush output regularly, enabling this option might degrade performance significantly on certain machines. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L488)\]

### OUTPUT\_FILE\_NAME*: string*

**Usage:** *OUTPUT\_FILE\_NAME {filename}*

Name of the output file. Relevant only if automatically started (through farming for example). If empty uses the project name as basis for it. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L384)\]

### PREFERRED\_CHOLESKY\_LIBRARY*: enum* *\= SCALAPACK*

**Usage:** *PREFERRED\_CHOLESKY\_LIBRARY DLAF*

**Valid values:**

-   `SCALAPACK` ScaLAPACK library

-   `SL` ScaLAPACK library (shorthand)

-   `DLAF` DLA-Future (CUDA/HIP GPU library)


**Mentions:** ⭐[DLA-Future](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/dlaf.html)

Specifies Cholesky decomposition library to be used. If not available, the ScaLAPACK library is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L152)\]

### PREFERRED\_DGEMM\_LIBRARY*: enum* *\= BLAS*

**Usage:** *PREFERRED\_DGEMM\_LIBRARY SPLA*

**Valid values:**

-   `SPLA` SPLA library

-   `BLAS` BLAS library


Specifies the DGEMM library to be used. If not available, the BLAS routine is used. This keyword affects some DGEMM calls in the WFC code and turns on their acceleration with SpLA. This keyword affects only local DGEMM calls, not the calls to PDGEMM (see keyword FM%TYPE\_OF\_MATRIX\_MULTIPLICATION). \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L172)\]

### PREFERRED\_DIAG\_LIBRARY*: enum* *\= ELPA*

**Usage:** *PREFERRED\_DIAG\_LIBRARY ELPA*

**Valid values:**

-   `ELPA` ELPA library

-   `SCALAPACK` ScaLAPACK library

-   `SL` ScaLAPACK library (shorthand)

-   `CUSOLVER` cuSOLVER (CUDA GPU library)

-   `DLAF` DLA-Future (CUDA/HIP GPU library)


**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html), ⭐[DLA-Future](https://manual.cp2k.org/cp2k-2026_2-branch/technologies/eigensolvers/dlaf.html)

Specifies the diagonalization library to be used. If not available, the ScaLAPACK library is used \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L124)\]

### PREFERRED\_FFT\_LIBRARY*: enum* *\= FFTW3*

**Usage:** *PREFERRED\_FFT\_LIBRARY FFTW3*

**Valid values:**

-   `FFTSG` Stefan Goedecker’s FFT (FFTSG), always available, will be used in case a FFT library is specified and not available.

-   `FFTW3` a fast portable FFT library. Recommended. See also the FFTW\_PLAN\_TYPE, and FFTW\_WISDOM\_FILE\_NAME keywords.

-   `FFTW` Same as FFTW3 (for compatibility with CP2K 2.3)


**References:** [Frigo2005](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#frigo2005)

**Mentions:** ⭐[Troubleshooting](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/troubleshooting.html)

Specifies the FFT library which should be preferred. If it is not available, use FFTW3 if this is linked in, if FFTW3 is not available use FFTSG. Improved performance with FFTW3 can be obtained specifying a proper value for FFTW\_PLAN\_TYPE. Contrary to earlier CP2K versions, all libraries will result in the same grids, i.e. the subset of grids which all FFT libraries can transform. See EXTENDED\_FFT\_LENGTHS if larger FFTs or grids that more precisely match a given cutoff are needed, or older results need to be reproduced. FFTW3 is often (close to) optimal, and well tested with CP2K. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L256)\]

### PRINT\_LEVEL*: enum* *\= MEDIUM*

**Aliases:** IOLEVEL

**Usage:** *PRINT\_LEVEL HIGH*

**Valid values:**

-   `SILENT` Almost no output

-   `LOW` Little output

-   `MEDIUM` Quite some output

-   `HIGH` Lots of output

-   `DEBUG` Everything is written out, useful for debugging purposes only


**Mentions:** ⭐[How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html), ⭐[HFX-RI with k-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/ri_kpoints.html)

How much output is written out. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L339)\]

### PROGRAM\_NAME*: enum* *\= CP2K*

**Aliases:** PROGRAM

**Usage:** *PROGRAM\_NAME {STRING}*

**Valid values:**

-   `ATOM` Runs single atom calculations

-   `FARMING` Runs N independent jobs in a single run

-   `TEST` Do some benchmarking and testing

-   `CP2K` Runs one of the CP2K package

-   `OPTIMIZE_INPUT` A tool to optimize parameters in a CP2K input

-   `OPTIMIZE_BASIS` A tool to create a MOLOPT or ADMM basis for a given set of training structures

-   `TMC` Runs Tree Monte Carlo algorithm using additional input file(s)

-   `MC_ANALYSIS` Runs (Tree) Monte Carlo trajectory file analysis

-   `SWARM` Runs swarm based calculation


Which program should be run \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L354)\]

### PROJECT\_NAME*: string* *\= PROJECT*

**Aliases:** PROJECT

**Usage:** *PROJECT\_NAME {STRING}*

**Mentions:** ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html)

Name of the project (used to build the name of the trajectory, and other files generated by the program) \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L375)\]

### RUN\_TYPE*: enum* *\= ENERGY\_FORCE*

**Usage:** *RUN\_TYPE MD*

**Valid values:**

-   `NONE` Perform no tasks

-   `ENERGY` Computes energy

-   `ENERGY_FORCE` Computes energy and forces

-   `MD` Molecular Dynamics

-   `GEO_OPT` Geometry Optimization

-   `MC` Monte Carlo

-   `DEBUG` Performs a Debug analysis

-   `BSSE` Basis set superposition error

-   `LR` Linear Response

-   `PINT` Path integral

-   `VIBRATIONAL_ANALYSIS` Vibrational analysis

-   `BAND` Band methods

-   `CELL_OPT` Cell optimization. Both cell vectors and atomic positions are optimised.

-   `WFN_OPT` Alias for ENERGY

-   `WAVEFUNCTION_OPTIMIZATION` Alias for ENERGY

-   `MOLECULAR_DYNAMICS` Alias for MD

-   `GEOMETRY_OPTIMIZATION` Alias for GEO\_OPT

-   `MONTECARLO` Alias for MC

-   `LINEAR_RESPONSE` Alias for LR

-   `NORMAL_MODES` Alias for VIBRATIONAL\_ANALYSIS

-   `RT_PROPAGATION` Real Time propagation run (fixed ionic positions)

-   `EHRENFEST_DYN` Ehrenfest dynamics (using real time propagation of the wavefunction)

-   `TAMC` Temperature Accelerated Monte Carlo (TAMC)

-   `TMC` Tree Monte Carlo (TMC), a pre-sampling MC algorithm

-   `DRIVER` i-PI driver mode

-   `NEGF` Non-equilibrium Green’s function method

-   `MIMIC` Run as a client in a simulation through the MiMiC framework

-   `RTP` Alias for RT\_PROPAGATION


**References:** [Ceriotti2014](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#ceriotti2014), [Schonherr2014](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#schonherr2014)

**Mentions:** ⭐[Run a First Calculation](https://manual.cp2k.org/cp2k-2026_2-branch/getting-started/first-calculation.html), ⭐[How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html), ⭐[Band structure from GW](https://manual.cp2k.org/cp2k-2026_2-branch/methods/electronic_structure/band/gw.html), ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html), ⭐[GW + Bethe-Salpeter equation](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/bethe-salpeter.html), ⭐[Time-Dependent DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/tddft.html), ⭐[Simulating Vibronic Effects in Optical Spectra](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/optical/vibronicspec.html), ⭐[X-Ray Absorption from TDDFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/properties/x-ray/tddft.html), ⭐[Real-Time Propagation and Ehrenfest MD](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/ehrenfest.html), ⭐[Molecular Dynamics](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/molecular_dynamics.html), ⭐[Monte Carlo](https://manual.cp2k.org/cp2k-2026_2-branch/methods/sampling/monte_carlo.html)

Selects the top-level task CP2K should run, such as an energy, energy-and-force, molecular dynamics, geometry optimization, or response calculation. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L393)\]

### SAVE\_MEM*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *SAVE\_MEM*

Some sections of the input structure are deallocated when not needed, and reallocated only when used. This reduces the required maximum memory. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L528)\]

### SEED*: integer\[ \]* *\= 2000*

**Usage:** *SEED {INTEGER} .. {INTEGER}*

Initial seed for the global (pseudo)random number generator to create a stream of normally Gaussian distributed random numbers. Exactly 1 or 6 positive integer values are expected. A single value is replicated to fill up the full seed array with 6 numbers. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L516)\]

### TRACE*: logical* *\= F*

**Lone keyword:** `T`

**Usage:** *TRACE*

If a debug trace of the execution of the program should be written \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L458)\]

### TRACE\_MASTER*: logical* *\= T*

**Lone keyword:** `T`

**Usage:** *TRACE\_MASTER*

For parallel TRACEd runs: only the master node writes output. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L465)\]

### TRACE\_MAX*: integer* *\= 2147483647*

**Usage:** *TRACE\_MAX 100*

Limit the total number a given subroutine is printed in the trace. Accounting is not influenced. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L473)\]

### TRACE\_ROUTINES*: string\[ \]*

**Usage:** *TRACE\_ROUTINES {routine\_name1} {routine\_name2} …*

A list of routines to trace. If left empty all routines are traced. Accounting is not influenced. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L480)\]

### WALLTIME*: string*

**Aliases:** WALLTI

**Usage:** *WALLTIME {real} or {HH:MM:SS}*

**Mentions:** ⭐[Geometry and cell optimization](https://manual.cp2k.org/cp2k-2026_2-branch/methods/optimization/geometry_and_cell_opt.html)

Maximum execution time for this run. Time in seconds or in HH:MM:SS. \[[Edit on GitHub](https://github.com/cp2k/cp2k/blob/master/src/input_cp2k_global.F#L430)\]
