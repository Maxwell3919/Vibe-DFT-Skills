# pw_user_guide.pdf — page 15

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `f2fa4e9584fb37ef7747b6d853569bb7433f6b2c9358377d11106c26e9e8c669`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
4.2    Memory requirements
A typical self-consistency or molecular-dynamics run requires a maximum memory in the order
of O double precision complex numbers, where

                          O = mM N + P N + pN1 N2 N3 + qNr1 Nr2 Nr3

with m, p, q = small factors; all other variables have the same meaning as above. Note that if
the Γ−point only (k = 0) is used to sample the Brillouin Zone, the value of N will be cut into
half.
    For hybrid DFTs, additional storage of Ox double precision complex numbers is needed (for
Fourier-transformed Kohn-Sham states), with Ox = xNq M N1 N2 N3 and x = 0.5 for Γ−only
calculations, x = 1 otherwise.
    The memory required by the phonon code follows the same patterns, with somewhat larger
factors m, p, q.

4.3    File space requirements
A typical pw.x run will require an amount of temporary disk space in the order of O double
precision complex numbers:
                                 O = Nk M N + qNr1 Nr2 Nr3
where q = 2× mixing ndim (number of iterations used in self-consistency, default value = 8) if
disk io is set to ’high’; q = 0 otherwise.

4.4    Parallelization issues
pw.x can run in principle on any number of processors. The effectiveness of parallelization is
ultimately judged by the ”scaling”, i.e. how the time needed to perform a job scales with the
number of processors, and depends upon:
    the size and type of the system under study;

    the judicious choice of the various levels of parallelization (detailed in Sec.4.4);

    the availability of fast interprocess communications (or lack of it).
Ideally one would like to have linear scaling, i.e. T ∼ T0 /Np for Np processors, where T0 is
the estimated time for serial execution. In addition, one would like to have linear scaling of
the RAM per processor: ON ∼ O0 /Np , so that large-memory systems fit into the RAM of each
processor.
   Parallelization on k-points:
    guarantees (almost) linear scaling if the number of k-points is a multiple of the number
     of pools;

    requires little communications (suitable for ethernet communications);

    reduces the required memory per processor by distributing wavefunctions (but not other
     quantities like the charge density). Does not hold if you set disk io=’high’.
Parallelization on PWs:

                                                15
```
