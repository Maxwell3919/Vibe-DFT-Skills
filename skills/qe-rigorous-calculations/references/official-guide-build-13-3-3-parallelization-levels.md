# 3.3 Parallelization levels

- Official source: https://www.quantum-espresso.org/Doc/user_guide/node20.html
- Retrieved: 2026-07-17T11:50:32+00:00
- Official source SHA-256: `87af80d7bb4593b465891b5d1ba8ee43c4386878d60310fc18a7e13f44950caf`
- Extracted text SHA-256: `ce617a3ec81bfbbd7dd86cd2f7ec6fb6561be3dc0e726ca7f2ad742627540495`
- Official Last-Modified: Mon, 08 Dec 2025 20:50:48 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

3.4 Understanding parallel I/O

Up:

3 Parallelism

Previous:

3.2 Running on parallel machines

  

Contents

Subsections

3.3.0.1 About communications

3.3.0.2 Choosing parameters

3.3.0.3 Massively parallel calculations

3.3 Parallelization levels

In Q
UANTUM 
ESPRESSO several MPI parallelization levels are
implemented, in which both calculations
and data structures are distributed across processors.
Processors are organized in a hierarchy of groups,
which are identified by different MPI communicators level.
The groups hierarchy is as follow:

world
: is the group of all processors (MPI_COMM_WORLD).

images
: Processors can then be divided into different "images", 
each corresponding to a different self-consistent or linear-response
calculation, loosely coupled to others. 

pools
: each image can be subpartitioned into
"pools", each taking care of a group of k-points.

bands
: each pool is subpartitioned into
"band groups", each taking care of a group
of Kohn-Sham orbitals (also called bands, or
wavefunctions). Especially useful for calculations
with hybrid functionals.

PW
: orbitals in the PW basis set,
as well as charges and density in either
reciprocal or real space, are distributed
across processors.
This is usually referred to as "PW parallelization".
All linear-algebra operations on array of PW /
real-space grids are automatically and effectively parallelized.
3D FFT is used to transform electronic wave functions from
reciprocal to real space and vice versa. The 3D FFT is
parallelized by distributing planes of the 3D grid in real
space to processors (in reciprocal space, it is columns of
G-vectors that are distributed to processors).

tasks
:
In order to allow good parallelization of the 3D FFT when
the number of processors exceeds the number of FFT planes,
FFTs on Kohn-Sham states are redistributed to
``task'' groups so that each group
can process several wavefunctions at the same time.
Alternatively, when this is not possible, a further
subdivision of FFT planes is performed.

linear-algebra group
:
A further level of parallelization, independent on
PW or k-point parallelization, is the parallelization of
subspace diagonalization / iterative orthonormalization.
Both operations required the diagonalization of
arrays whose dimension is the number of Kohn-Sham states
(or a small multiple of it). All such arrays are distributed block-like
across the ``linear-algebra group'', a subgroup of the pool of processors,
organized in a square 2D grid. As a consequence the number of processors
in the linear-algebra group is given by 
n
2
, where 
n
is an integer;

n
2
must be smaller than the number of processors in the PW group.
The diagonalization is then performed
in parallel using standard linear algebra operations.
(This diagonalization is used by, but should not be confused with,
the iterative Davidson algorithm). The preferred option is to use
ELPA and ScaLAPACK; alternative built-in algorithms are anyway available.

Note however that not all parallelization levels
are implemented in all codes.

When a communicator is split, the MPI process IDs in each sub-communicator
remain ordered. So for instance, for two images and 2
n
MPI processes,
image 0 contains IDs 

0, 1,..., 
n
- 1, image 1 contains IDs 

n
, 
n
+ 1,.., 2
n
- 1.

3.3.0.1 About communications

Images and pools are loosely coupled: inter-processors communication
between different images and pools is modest. Processors within each
pool are instead tightly coupled and communications are significant.
This means that fast communication hardware is needed if
your pool extends over more than a few processors on different nodes.

3.3.0.2 Choosing parameters

:
To control the number of processors in each group,
command line switches:

-nimage
, 
-npools
, 
-nband
,

-ntg
, 
-ndiag
or 
-northo

(shorthands, respectively: 
-ni
, 
-nk
, 
-nb
,

-nt
, 
-nd
)
are used.
As an example consider the following command line:

mpirun -np 4096 ./neb.x -ni 8 -nk 2 -nt 4 -nd 144 -i my.input

This executes a NEB calculation on 4096 processors, 8 images (points in the configuration
space in this case) at the same time, each of
which is distributed across 512 processors.
k-points are distributed across 2 pools of 256 processors each,
3D FFT is performed using 4 task groups (64 processors each, so
the 3D real-space grid is cut into 64 slices), and the diagonalization
of the subspace Hamiltonian is distributed to a square grid of 144
processors (12x12).

Default values are: 
-ni 1 -nk 1 -nt 1
;

nd
is set to 1 if ScaLAPACK is not compiled,
it is set to the square integer smaller than or equal to the number of
processors of each pool.

3.3.0.3 Massively parallel calculations

For very large jobs (i.e. O(1000) atoms or more) or for very long jobs,
to be run on massively parallel machines (e.g. IBM BlueGene) it is
crucial to use in an effective way all available parallelization levels:
on linear algebra (requires compilation with ELPA and/or ScaLAPACK),
on "task groups" (requires run-time option "-nt N"), and mixed
MPI-OpenMP (requires OpenMP compilation: 
configure
–enable-openmp).
Without a judicious choice of parameters, large jobs will find a
stumbling block in either memory or CPU requirements. Note that I/O
may also become a limiting factor.

next 

up 

previous 

contents 

Next:

3.4 Understanding parallel I/O

Up:

3 Parallelism

Previous:

3.2 Running on parallel machines

  

Contents
```
