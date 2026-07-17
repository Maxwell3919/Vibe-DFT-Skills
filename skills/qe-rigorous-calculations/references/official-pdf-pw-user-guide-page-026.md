# pw_user_guide.pdf — page 26

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `4059cb7e539e9de0c96da07252697f041c54c8193decd6122eca487c39d18335`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   2. Reduce mixing beta to ∼ 0.3 ÷ 0.1 or smaller. Try the mixing mode value that is more
      appropriate for your problem. For slab geometries used in surface problems or for elon-
      gated cells, mixing mode=’local-TF’ should be the better choice, dampening ”charge
      sloshing”. You may also try to increase mixing ndim to more than 8 (default value).
      Beware: this will increase the amount of memory you need.

   3. Specific to USPP: the presence of negative charge density regions due to either the
      pseudization procedure of the augmentation part or to truncation at finite cutoff may
      give convergence problems. Raising the ecutrho cutoff for charge density will usually
      help.

I do not get the same results in different machines! If the difference is small, do not
panic. It is quite normal for iterative methods to reach convergence through different paths
as soon as anything changes. In particular, between serial and parallel execution there are
operations that are not performed in the same order. As the numerical accuracy of computer
numbers is finite, this can yield slightly different results.
    It is also normal that the total energy converges to a better accuracy than its terms, since
only the sum is variational, i.e. has a minimum in correspondence to ground-state charge
density. Thus if the convergence threshold is for instance 10−8 , you get 8-digit accuracy on
the total energy, but one or two less on other terms (e.g. XC and Hartree energy). It this
is a problem for you, reduce the convergence threshold for instance to 10−10 or 10−12 . The
differences should go away (but it will probably take a few more iterations to converge).

Execution time is time-dependent! Yes it is! On most machines and on most operating
systems, depending on machine load, on communication load (for parallel machines), on various
other factors (including maybe the phase of the moon), reported execution times may vary quite
a lot for the same job.

Warning : N eigenvectors not converged This is a warning message that can be safely
ignored if it is not present in the last steps of self-consistency. If it is still present in the last
steps of self-consistency, and if the number of unconverged eigenvector is a significant part of
the total, it may signal serious trouble in self-consistency (see next point) or something badly
wrong in input data.

Warning : negative or imaginary charge..., or ...core charge ..., or npt with
rhoup< 0... or rho dw< 0... These are warning messages that can be safely ignored unless
the negative or imaginary charge is sizable, let us say of the order of 0.1. If it is, something
seriously wrong is going on. Otherwise, the origin of the negative charge is the following. When
one transforms a positive function in real space to Fourier space and truncates at some finite
cutoff, the positive function is no longer guaranteed to be positive when transformed back to
real space. This happens only with core corrections and with USPPs. In some cases it may
be a source of trouble (see next point) but it is usually solved by increasing the cutoff for the
charge density.

Structural optimization is slow or does not converge or ends with a mysterious
bfgs error Typical structural optimizations, based on the BFGS algorithm, converge to the


                                                 26
```
