# neb_user_guide.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/neb_user_guide.pdf
- Retrieved: 2026-07-17T11:53:27+00:00
- Official source SHA-256: `acc9df963f4b8009b54b8f253bf207386ed0fd2793881764886022af09c58d2a`
- Extracted text SHA-256: `7295683da2be6bae2c18a3527f4694a11d80f1fb12fd33d781dfc328df66b342`
- Official Last-Modified: Mon, 08 Dec 2025 21:37:56 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    6. A gross estimate of the required number of iterations is (number of images) * (number of
       atoms) * 3. Atoms that do not move should not be counted. It may take half that many
       iterations, or twice as many, but more or less that’s the order of magnitude, unless one
       starts from a very good or very bad initial guess.

   The code path int.x is is a tool to generate a new path (what is actually generated is
the restart file) starting from an old one through interpolation (cubic splines). The new path
can be discretized with a different number of images (this is its main purpose), images are
equispaced and the interpolation can be also performed on a subsection of the old path. The
input file needed by path int.x can be easily set up with the help of the self-explanatory
path interpolation.sh shell script in the NEB/tools folder.


6     Performances
PWneb requires roughly the time and memory needed for a single SCF calculation, times
num of images, times the number of NEB iterations needed to reach convergence. We refer the
reader to the PW user guide for more information.


7     Troubleshooting
Almost all problems in PWneb arise from incorrect input data and result in error stops. Error
messages should be self-explanatory, but unfortunately this is not always true. If the code
issues a warning messages and continues, pay attention to it but do not assume that something
is necessarily wrong in your calculation: most warning messages signal harmless problems.




                                               6
```
