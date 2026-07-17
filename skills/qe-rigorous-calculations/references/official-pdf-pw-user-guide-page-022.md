# pw_user_guide.pdf — page 22

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `0834ce9fbd2f7bab5a812216a37396cf4b490fb9ffb46d2a05ce4e6076b0e356`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
pw.x crashes with no error message at all This happens quite often in parallel execu-
tion, or under a batch queue, or if you are writing the output to a file. When the program
crashes, part of the output, including the error message, may be lost, or hidden into error files
where nobody looks into. It is the fault of the operating system, not of the code. Try to run
interactively and to write to the screen. If this doesn’t help, move to next point.

pw.x crashes with segmentation fault or similarly obscure messages Possible rea-
sons:

    too much RAM memory or stack requested (see next item).

    if you are using highly optimized mathematical libraries, verify that they are designed for
     your hardware.

    If you are using aggressive optimization in compilation, verify that you are using the
     appropriate options for your machine

    the executable was not properly compiled, or was compiled on a different and incompatible
     environment.

    buggy compiler or libraries: this is the default explanation if you have problems with the
     provided tests and examples.

pw.x works for simple systems, but not for large systems or whenever more RAM
is needed Possible solutions:

    Increase the amount of RAM you are authorized to use (which may be much smaller than
     the available RAM). Ask your system administrator if you don’t know what to do. In
     some cases the stack size can be a source of problems: if so, increase it with command
     limits or ulimit).

    Reduce nbnd to the strict minimum (for insulators, the default is already the minimum,
     though).

    Reduce the work space for Davidson diagonalization to the minimum by setting diago david ndim=
     also consider using conjugate gradient diagonalization (diagonalization=’cg’), slow but
     very robust, which requires almost no work space.

    If the charge density takes a significant amount of RAM, reduce mixing ndim from its
     default value (8) to 4 or so.

    In parallel execution, use more processors, or use the same number of processors with less
     pools. Remember that parallelization with respect to k-points (pools) does not distribute
     memory: only parallelization with respect to R- (and G-) space does.

    If none of the above is sufficient or feasible, you have to either reduce the cutoffs and/or
     the cell size, or to use a machine with more RAM.




                                               22
```
