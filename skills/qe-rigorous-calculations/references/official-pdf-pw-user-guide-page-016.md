# pw_user_guide.pdf — page 16

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `1ae3ab722689011fb5b885b317cf2b65cc82a15a21d991f3f282d6f7f7a15799`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    yields good to very good scaling, especially if the number of processors in a pool is a
     divisor of N3 and Nr3 (the dimensions along the z-axis of the FFT grids, nr3 and nr3s,
     which coincide for NCPPs);

    requires heavy communications (suitable for Gigabit ethernet up to 4, 8 CPUs at most,
     specialized communication hardware needed for 8 or more processors );

    yields almost linear reduction of memory per processor with the number of processors in
     the pool.
    A note on scaling: optimal serial performances are achieved when the data are as much as
possible kept into the cache. As a side effect, PW parallelization may yield superlinear (better
than linear) scaling, thanks to the increase in serial speed coming from the reduction of data
size (making it easier for the machine to keep data in the cache).
    VERY IMPORTANT: For each system there is an optimal range of number of processors on
which to run the job. A too large number of processors will yield performance degradation. If
the size of pools is especially delicate: Np should not exceed N3 and Nr3 , and should ideally be
no larger than 1/2 ÷ 1/4N3 and/or Nr3 . In order to increase scalability, it is often convenient
to further subdivide a pool of processors into ”task groups”. When the number of processors
exceeds the number of FFT planes, data can be redistributed to ”task groups” so that each
group can process several wavefunctions at the same time.
    The optimal number of processors for ”linear-algebra” parallelization, taking care of mul-
tiplication and diagonalization of M × M matrices, should be determined by observing the
performances of cdiagh/rdiagh (pw.x) or ortho (cp.x) for different numbers of processors in
the linear-algebra group (must be a square integer).
    Actual parallel performances will also depend on the available software (MPI libraries) and
on the available communication hardware. For PC clusters, OpenMPI (http://www.openmpi.org/)
seems to yield better performances than other implementations (info by Kostantin Kudin). Note
however that you need a decent communication hardware (at least Gigabit ethernet) in order
to have acceptable performances with PW parallelization. Do not expect good scaling with
cheap hardware: PW calculations are by no means an ”embarrassing parallel” problem.
    Also note that multiprocessor motherboards for Intel Pentium CPUs typically have just one
memory bus for all processors. This dramatically slows down any code doing massive access to
memory (as most codes in the Quantum ESPRESSO distribution do) that runs on processors
of the same motherboard.

4.5     Understanding the time report
The time report printed at the end of a pw.x run contains a lot of useful information that can
be used to understand bottlenecks and improve performances.

4.5.1   Serial execution
The following applies to calculations taking a sizable amount of time (at least minutes): for short
calculations (seconds), the time spent in the various initializations dominates. Any discrepancy
with the following picture signals some anomaly.

    For a typical job with norm-conserving PPs, the total (wall) time is mostly spent in
     routine ”electrons”, calculating the self-consistent solution.

                                                16
```
