# user_guide.pdf — page 28

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `6262a185bb665a4db1c2a3a0e11437df7617e9d47f8083bc541c63e39b830bb2`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
About communications Images and pools are loosely coupled: inter-processors communi-
cation between different images and pools is modest. Processors within each pool are instead
tightly coupled and communications are significant. This means that fast communication hard-
ware is needed if your pool extends over more than a few processors on different nodes.

Choosing parameters : To control the number of processors in each group, command line
switches: -nimage, -npools, -nband, -ntg, -ndiag or -northo (shorthands, respectively: -ni,
-nk, -nb, -nt, -nd) are used. As an example consider the following command line:
mpirun -np 4096 ./neb.x -ni 8 -nk 2 -nt 4 -nd 144 -i my.input
This executes a NEB calculation on 4096 processors, 8 images (points in the configuration space
in this case) at the same time, each of which is distributed across 512 processors. k-points are
distributed across 2 pools of 256 processors each, 3D FFT is performed using 4 task groups (64
processors each, so the 3D real-space grid is cut into 64 slices), and the diagonalization of the
subspace Hamiltonian is distributed to a square grid of 144 processors (12x12).
    Default values are: -ni 1 -nk 1 -nt 1 ; nd is set to 1 if ScaLAPACK is not compiled, it
is set to the square integer smaller than or equal to the number of processors of each pool.

Massively parallel calculations For very large jobs (i.e. O(1000) atoms or more) or for
very long jobs, to be run on massively parallel machines (e.g. IBM BlueGene) it is crucial to use
in an effective way all available parallelization levels: on linear algebra (requires compilation
with ELPA and/or ScaLAPACK), on ”task groups” (requires run-time option ”-nt N”), and
mixed MPI-OpenMP (requires OpenMP compilation: configure–enable-openmp). Without a
judicious choice of parameters, large jobs will find a stumbling block in either memory or CPU
requirements. Note that I/O may also become a limiting factor.

3.4    Understanding parallel I/O
In parallel execution, each processor has its own slice of data (Kohn-Sham orbitals, charge
density, etc), that have to be written to temporary files during the calculation, or to data files
at the end of the calculation. This can be done in two different ways:
   • “collected”: all slices are collected by the code to a single processor that writes them to
     disk, in a single file, using a format that doesn’t depend upon the number of processors
     or their distribution. This is the default since v.6.2 for final data.
   • “portable”: as above, but data can be copied to and read from a different machines
     (this is not guaranteed with Fortran binary files). Requires compilation with -D__HDF5
     preprocessing option and HDF5 libraries.
There is a third format, no longer used for final data but used for scratch and restart files:
   • “distributed”: each processor writes its own slice to disk in its internal format to a
     different file. The “distributed” format is fast and simple, but the data so produced is
     readable only by a job running on the same number of processors, with the same type of
     parallelization, as the job who wrote the data, and if all files are on a file system that is
     visible to all processors (i.e., you cannot use local scratch directories: there is presently
     no way to ensure that the distribution of processes across processors will follow the same
     pattern for different jobs).

                                               28
```
