# pw_user_guide.pdf — page 18

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `fafefd60e275d8c48673e311339f254f0c9ad91272fe94d96ec9e76ae65a6e10`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    CPU and wall time do not differ by much, if OpenMP is not active, or: CPU time
     approaches wall time times the number of OpenMP threads, if OpenMP is active.

    Time usage is still dominated by the same routines as for the serial run.

    Routine ”fft scatter” (called by parallel FFT) takes a sizable part of the time spent in
     FFTs but does not dominate it.

Quick estimate of parallelization parameters You need to know

    the number of k-points, Nk

    the third dimension of the (smooth) FFT grid, N3

    the number of Kohn-Sham states, M

These data allow to set bounds on parallelization:

    k-point parallelization is limited to Nk processor pools: -nk Nk

    FFT parallelization shouldn’t exceed N3 processors, i.e. if you run with -nk Nk, use
     N = Nk × N3 MPI processes at most (mpirun -np N ...)

    Unless M is a few hundreds or more, don’t bother using linear-algebra parallelization

You will need to experiment a bit to find the best compromise. In order to have good load
balancing among MPI processes, the number of k-point pools should be an integer divisor of
Nk ; the number of processors for FFT parallelization should be an integer divisor of N3 .

Automatic guess of parallelization parameters Since v.7.1, the code tries to guess a
reasonable set of parameters for the k-point, linear-algebra, and task-group parallelizations, if
they are not explicitly provided in the command line. The logic is as follows:

    if the number of processors Np exceeds N3 , one uses k-point parallelization on the smallest
     number Nk such that Np /Nk ≤ N3 /2;

    if the number of processors Np /Nk still exceeds N3 , one uses task-group parallelization
     on the smallest Nt that ensures Np /Nk /Nt ≤ N3 /4;

    linear-algebra parallelization is done on n2d processors (n2d ≤ Np /Nk /Nt ) with nd such that
     M/nd ∼ 100.

Typical symptoms of bad/inadequate parallelization

    a large fraction of time is spent in ”v of rho”, ”newd”, ”mix rho”, or
     the time doesn’t scale well or doesn’t scale at all by increasing the number of processors
     for k-point parallelization. Solution:

        – use (also) FFT parallelization if possible

    a disproportionate time is spent in ”cdiaghg”/”rdiaghg”. Solutions:


                                               18
```
