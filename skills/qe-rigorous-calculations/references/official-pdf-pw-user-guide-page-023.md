# pw_user_guide.pdf — page 23

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `6785aa499b568917020100265da2e206f36c0d39ad0794aaffe232a9499f7dc9`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
pw.x crashes with error in davcio davcio is the routine that performs most of the I/O
operations (read from disk and write to disk) in pw.x; error in davcio means a failure of an
I/O operation.

    If the error is reproducible and happens at the beginning of a calculation: check if you
     have read/write permission to the scratch directory specified in variable outdir. Also:
     check if there is enough free space available on the disk you are writing to, and check your
     disk quota (if any).

    If the error is irreproducible: your might have flaky disks; if you are writing via the
     network using NFS (which you shouldn’t do anyway), your network connection might be
     not so stable, or your NFS implementation is unable to work under heavy load

    If it happens while restarting from a previous calculation: you might be restarting from
     the wrong place, or from wrong data, or the files might be corrupted. Note that, since
     QE 5.1, restarting from arbitrary places is no more supported: the code must terminate
     cleanly.

    If you are running two or more instances of pw.x at the same time, check if you are using
     the same file names in the same temporary directory. For instance, if you submit a series
     of jobs to a batch queue, do not use the same outdir and the same prefix, unless you
     are sure that one job doesn’t start before a preceding one has finished.

pw.x crashes in parallel execution with an obscure message related to MPI errors
Random crashes due to MPI errors have often been reported, typically in Linux PC clusters.
We cannot rule out the possibility that bugs in Quantum ESPRESSO cause such behavior,
but we are quite confident that the most likely explanation is a hardware problem (defective
RAM for instance) or a software bug (in MPI libraries, compiler, operating system).
   Debugging a parallel code may be difficult, but you should at least verify if your problem is
reproducible on different architectures/software configurations/input data sets, and if there is
some particular condition that activates the bug. If this doesn’t seem to happen, the odds are
that the problem is not in Quantum ESPRESSO. You may still report your problem, but
consider that reports like it crashes with...(obscure MPI error) contain 0 bits of information
and are likely to get 0 bits of answers.

pw.x stops with error message the system is metallic, specify occupations You did
not specify state occupations, but you need to, since your system appears to have an odd number
of electrons. The variable controlling how metallicity is treated is occupations in namelist
&SYSTEM. The default, occupations=’fixed’, occupies the lowest (N electrons)/2 states
and works only for insulators with a gap. In all other cases, use ’smearing’ (’tetrahedra’
for DOS calculations). See input reference documentation for more details.

pw.x stops with internal error: cannot bracket Ef Possible reasons:

    serious error in data, such as bad number of electrons, insufficient number of bands,
     absurd value of broadening;




                                               23
```
