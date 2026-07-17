# pw_user_guide.pdf — page 14

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `f9b89aaf9c49c16711c5c582d4f77666157936e4f998054e5ac8b9ef0b7f94a8`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   The time required for a single self-consistency iteration Titer is:
                                  Titer = Nk Tdiag + Trho + Tscf
where Nk = number of k-points, Tdiag = time per Hamiltonian iterative diagonalization, Trho
= time for charge density calculation, Tscf = time for Hartree and XC potential calculation.
   The time for a Hamiltonian iterative diagonalization Tdiag is:
                                   Tdiag = Nh Th + Torth + Tsub
where Nh = number of Hψ products needed by iterative diagonalization, Th = time per Hψ
product, Torth = CPU time for orthonormalization, Tsub = CPU time for subspace diagonaliza-
tion.
    The time Th required for a Hψ product is
                     Th = a1 M N + a2 M N1 N2 N3 log(N1 N2 N3 ) + a3 M P N.
The first term comes from the kinetic term and is usually much smaller than the others. The
second and third terms come respectively from local and nonlocal potential. a1 , a2 , a3 are
prefactors (i.e. small numbers O(1)), M = number of valence bands (nbnd), N = number of
PW (basis set dimension: npw), N1 , N2 , N3 = dimensions of the FFT grid for wavefunctions
(nr1s, nr2s, nr3s; N1 N2 N3 ∼ 8N ), P = number of pseudopotential projectors, summed on
all atoms, on all values of the angular momentum l, and m = 1, ..., 2l + 1.
    The time Torth required by orthonormalization is
                                         Torth = b1 N Mx2
and the time Tsub required by subspace diagonalization is
                                           Tsub = b2 Mx3
where b1 and b2 are prefactors, Mx = number of trial wavefunctions (this will vary between M
and 2 ÷ 4M , depending on the algorithm).
   The time Trho for the calculation of charge density from wavefunctions is
                 Trho = c1 M Nr1 Nr2 Nr3 log(Nr1 Nr2 Nr3 ) + c2 M Nr1 Nr2 Nr3 + Tus
where c1 , c2 , c3 are prefactors, Nr1 , Nr2 , Nr3 = dimensions of the FFT grid for charge density
(nr1, nr2, nr3; Nr1 Nr2 Nr3 ∼ 8Ng , where Ng = number of G-vectors for the charge density,
ngm), and Tus = time required by PAW/USPPs contribution (if any). Note that for NCPPs
the FFT grids for charge and wavefunctions are the same.
   The time Tscf for calculation of potential from charge density is
                      Tscf = d2 Nr1 Nr2 Nr3 + d3 Nr1 Nr2 Nr3 log(Nr1 Nr2 Nr3 )
where d1 , d2 are prefactors.
   For hybrid DFTs, the dominant term is by far the calculation of the nonlocal (Vx ψ) product,
taking as much as
                              Texx = eNk Nq M 2 N1 N2 N3 log(N1 N2 N3 )
where Nq is the number of points in the k + q grid, determined by options nqx1,nqx2,nqx3, e
is a prefactor.
    The above estimates are for serial execution. In parallel execution, each contribution may
scale in a different manner with the number of processors (see below).

                                                14
```
