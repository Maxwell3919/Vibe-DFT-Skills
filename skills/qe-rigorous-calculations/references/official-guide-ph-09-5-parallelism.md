# 5 Parallelism

- Official source: https://www.quantum-espresso.org/Doc/ph_user_guide/node17.html
- Retrieved: 2026-07-17T11:51:44+00:00
- Official source SHA-256: `0be44a6a8f56b7b180075d4f2bbdf8a026533c7eb9edaf09235ae0196367c72c`
- Extracted text SHA-256: `2d15e98ca8ddda7a4830b5005fde0f9d2455923c0403fabba5079cd952e9629b`
- Official Last-Modified: Tue, 14 Oct 2025 10:25:49 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

6 Troubleshooting

Up:

User's Guide for the PHonon

Previous:

4.9 Calculation of phonon-renormalization of

  

Contents

5 Parallelism

We refer to the corresponding section of the 
PWscf
guide for
an explanation of how parallelism works. 

ph.x
may take advantage of MPI parallelization on images, plane waves (PW) 
and on 
k
-points (``pools''). Currently all other MPI and explicit 
OpenMP parallelizations have very limited to nonexistent implementation.

phcg.x
implements only PW parallelization.
All other codes may be launched in parallel, but will execute 
on a single processor.

In ``image'' parallelization, processors can be divided into different 
``images", corresponding to one (or more than one) ``irrep'' or 
q

vectors. Images are loosely coupled: processors communicate
between different images only once in a while, so image parallelization
is suitable for cheap communication hardware (e.g. Gigabit Ethernet).
Image parallelization is activated by specifying the option 

-nimage N
to 
ph.x
. Inside an image, PW and 
k
-point 
parallelization can be performed: for instance,

mpirun -np 64 ph.x -ni 8 -nk 2 ...

will run 8 images on 8 processors each, subdivided into 2 pools 
of 4 processors for 
k
-point parallelization. In order 
to run the 
ph.x
code with these flags the 
pw.x
run has to be run with:

mpirun -np 8 pw.x -nk 2 ...

without any 
-nimage
flag. 
After the phonon calculation with images the dynmical matrices of 

q
-vectors calculated in different images are not present in the
working directory. To obtain them you need to run 

ph.x
again with:

mpirun -np 8 ph.x -nk 2 ...

and the 
recover=.true.
flag. This scheme is quite automatic and
does not require any additional work by the user, but it wastes some 
CPU time because all images stops when the image that requires the 
largest amount of time finishes the calculation. Load balancing 
between images is still at
an experimental stage. You can look into the routine 
image_q_irr

inside 
PHonon/PH/check_initial_status
to see the present
algorithm for work distribution and modify it if you think that
you can improve the load balancing.

A different paradigm is the usage of the GRID concept, instead of MPI,
to achieve parallelization over irreps and 
q
vectors.
Complete phonon dispersion calculation can be quite long and
expensive, but it can be split into a number of semi-independent
calculations, using options 
start_q
, 
last_q
,

start_irr
, 
last_irr
. An example on how to
distribute the calculations and collect the results can be found
in 
examples/GRID_example
. Reference:

Calculation of Phonon Dispersions on the GRID using Quantum
ESPRESSO
,
R. di Meo, A. Dal Corso, P. Giannozzi, and S. Cozzini, in

Chemistry and Material Science Applications on Grid Infrastructures
,
editors: S. Cozzini, A. Laganà, ICTP Lecture Notes Series,
Vol. 24, pp.165-183 (2009).

next 

up 

previous 

contents 

Next:

6 Troubleshooting

Up:

User's Guide for the PHonon

Previous:

4.9 Calculation of phonon-renormalization of

  

Contents
```
