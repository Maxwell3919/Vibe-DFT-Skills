# ph_user_guide.pdf — page 9

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `2aac65225b23b9bb53652f37fead821d8c4b4b72bf073c8386adf3ffd68defd7`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
municate between different images only once in a while, so image parallelization is suitable for
cheap communication hardware (e.g. Gigabit Ethernet). Image parallelization is activated by
specifying the option -nimage N to ph.x. Inside an image, PW and k-point parallelization can
be performed: for instance,

    mpirun -np 64 ph.x -ni 8 -nk 2 ...

will run 8 images on 8 processors each, subdivided into 2 pools of 4 processors for k-point
parallelization. In order to run the ph.x code with these flags the pw.x run has to be run with:

    mpirun -np 8 pw.x -nk 2 ...

without any -nimage flag. After the phonon calculation with images the dynmical matrices
of q-vectors calculated in different images are not present in the working directory. To obtain
them you need to run ph.x again with:

    mpirun -np 8 ph.x -nk 2 ...

and the recover=.true. flag. This scheme is quite automatic and does not require any
additional work by the user, but it wastes some CPU time because all images stops when
the image that requires the largest amount of time finishes the calculation. Load balancing
between images is still at an experimental stage. You can look into the routine image q irr
inside PHonon/PH/check initial status to see the present algorithm for work distribution
and modify it if you think that you can improve the load balancing.
    A different paradigm is the usage of the GRID concept, instead of MPI, to achieve paral-
lelization over irreps and q vectors. Complete phonon dispersion calculation can be quite long
and expensive, but it can be split into a number of semi-independent calculations, using options
start q, last q, start irr, last irr. An example on how to distribute the calculations and
collect the results can be found in examples/GRID example. Reference:
Calculation of Phonon Dispersions on the GRID using Quantum ESPRESSO, R. di Meo, A.
Dal Corso, P. Giannozzi, and S. Cozzini, in Chemistry and Material Science Applications on
Grid Infrastructures, editors: S. Cozzini, A. Laganà, ICTP Lecture Notes Series, Vol. 24,
pp.165-183 (2009).


6    Troubleshooting
ph.x stops with error reading file The data file produced by pw.x is bad or incomplete
or produced by an incompatible version of the code.

ph.x mumbles something like cannot recover or error reading recover file You have
a bad restart file from a preceding failed execution. Remove all files recover* in outdir.

ph.x says occupation numbers probably wrong and continues You have a metallic or
spin-polarized system but occupations are not set to ‘smearing’.




                                               9
```
