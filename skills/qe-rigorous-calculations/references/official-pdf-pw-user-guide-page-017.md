# pw_user_guide.pdf — page 17

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `3010fe2e3976200e369f4a6c2aefe9efd5d7de0d249c1c9ff8fcae4c02057ce1`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    Most of the time spent in ”electrons” is used by routine ”c bands”, calculating Kohn-
     Sham states. ”sum band” (calculating the charge density), ”v of rho” (calculating the
     potential), ”mix rho” (charge density mixing) should take a small fraction of the time.

    Most of the time spent in ”c bands” is used by routines ”cegterg” (k-points) or ”regterg”
     (Gamma-point only), performing iterative diagonalization of the Kohn-Sham Hamiltonian
     in the PW basis set.

    Most of the time spent in ”*egterg” is used by routine ”h psi”, calculating Hψ products.
     ”cdiaghg” (k-points) or ”rdiaghg” (Gamma-only), performing subspace diagonalization,
     should take only a small fraction.

    Among the ”general routines”, most of the time is spent in FFT on Kohn-Sham states:
     ”fftw”, and to a smaller extent in other FFTs, ”fft” and ”ffts”, and in ”calbec”, calculating
     ⟨ψ|β⟩ products.

    Forces and stresses typically take a fraction of the order of 10 to 20% of the total time.

For PAW and Ultrasoft PP, you will see a larger contribution by ”sum band” and a nonnegligible
”newd” contribution to the time spent in ”electrons”, but the overall picture is unchanged. You
may drastically reduce the overhead of Ultrasoft PPs by using input option ”tqr=.true.”.

4.5.2   Parallel execution
The various parallelization levels should be used wisely in order to achieve good results. Let
us summarize the effects of them on CPU:

    Parallelization on FFT speeds up (with varying efficiency) almost all routines, with the
     notable exception of ”cdiaghg” and ”rdiaghg”.

    Parallelization on k-points speeds up (almost linearly) ”c bands” and called routines;
     speeds up partially ”sum band”; does not speed up at all ”v of rho”, ”newd”, ”mix rho”.

    Linear-algebra parallelization speeds up (not always) ”cdiaghg” and ”rdiaghg”.

    ”task-group” parallelization speeds up ”fftw”.

    OpenMP parallelization speeds up ”fftw”, plus selected parts of the calculation, plus
     (depending on the availability of OpenMP-aware libraries) some linear algebra operations.

and on RAM:

    Parallelization on FFT distributes most arrays across processors (i.e. all G-space and R-
     spaces arrays) but not all of them (in particular, not subspace Hamiltonian and overlap
     matrices).

    Linear-algebra parallelization also distributes subspace Hamiltonian and overlap matrices.

    All other parallelization levels do not distribute any memory.

In an ideally parallelized run, you should observe the following:


                                               17
```
