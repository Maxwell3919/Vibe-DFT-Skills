# user_guide.pdf — page 27

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `f8bc1f56e4181a6d872c2a1102e4c0b292b910a68701cba6c0d985ec7e1078b7`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3.3    Parallelization levels
In Quantum ESPRESSO several MPI parallelization levels are implemented, in which both
calculations and data structures are distributed across processors. Processors are organized in
a hierarchy of groups, which are identified by different MPI communicators level. The groups
hierarchy is as follow:

   • world: is the group of all processors (MPI COMM WORLD).

   • images: Processors can then be divided into different ”images”, each corresponding to a
     different self-consistent or linear-response calculation, loosely coupled to others.

   • pools: each image can be subpartitioned into ”pools”, each taking care of a group of
     k-points.

   • bands: each pool is subpartitioned into ”band groups”, each taking care of a group of
     Kohn-Sham orbitals (also called bands, or wavefunctions). Especially useful for calcula-
     tions with hybrid functionals.

   • PW: orbitals in the PW basis set, as well as charges and density in either reciprocal or real
     space, are distributed across processors. This is usually referred to as ”PW paralleliza-
     tion”. All linear-algebra operations on array of PW / real-space grids are automatically
     and effectively parallelized. 3D FFT is used to transform electronic wave functions from
     reciprocal to real space and vice versa. The 3D FFT is parallelized by distributing planes
     of the 3D grid in real space to processors (in reciprocal space, it is columns of G-vectors
     that are distributed to processors).

   • tasks: In order to allow good parallelization of the 3D FFT when the number of processors
     exceeds the number of FFT planes, FFTs on Kohn-Sham states are redistributed to
     “task” groups so that each group can process several wavefunctions at the same time.
     Alternatively, when this is not possible, a further subdivision of FFT planes is performed.

   • linear-algebra group: A further level of parallelization, independent on PW or k-point
     parallelization, is the parallelization of subspace diagonalization / iterative orthonormal-
     ization. Both operations required the diagonalization of arrays whose dimension is the
     number of Kohn-Sham states (or a small multiple of it). All such arrays are distributed
     block-like across the “linear-algebra group”, a subgroup of the pool of processors, orga-
     nized in a square 2D grid. As a consequence the number of processors in the linear-algebra
     group is given by n2 , where n is an integer; n2 must be smaller than the number of proces-
     sors in the PW group. The diagonalization is then performed in parallel using standard
     linear algebra operations. (This diagonalization is used by, but should not be confused
     with, the iterative Davidson algorithm). The preferred option is to use ELPA and ScaLA-
     PACK; alternative built-in algorithms are anyway available.

Note however that not all parallelization levels are implemented in all codes.
    When a communicator is split, the MPI process IDs in each sub-communicator remain
ordered. So for instance, for two images and 2n MPI processes, image 0 contains IDs 0, 1, ..., n−
1, image 1 contains IDs n, n + 1, .., 2n − 1.




                                               27
```
