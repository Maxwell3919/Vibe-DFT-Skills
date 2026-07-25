# CP2K official manual snapshot: dft-methods

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/index.html
- Raw SHA-256: 4e8db05ef1fa7ef41f476bbb7fe0a38b4feee025566d787e1770fb664788d559
- Converter: helloworld-Co/html2md at `ca08965af93e6565806a79087868daa439565ffc`; adapter schema `1.0`.
- Status: version-matched cached official text; reopen the source for current live verification.

---

# Density Functional Theory

-   [Gaussian Plane Wave](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gpw.html)
-   [Gaussian Augmented Plane Waves](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gapw.html)
-   [Hartree-Fock Exchange](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/index.html)
    -   [HFX with ADMM](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/admm.html)
    -   [HFX-RI for Γ-Point (non-periodic)](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/ri_gamma.html)
    -   [HFX-RI with k-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/ri_kpoints.html)
-   [Basis Sets](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/basis_sets.html)
-   [Pseudopotentials](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/pseudopotentials.html)
-   [K-Points](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/k-points.html)
-   [How to make a SCF run converge](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/convergence.html)
-   [How to Converge the CUTOFF and REL\_CUTOFF](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cutoff.html)
-   [Local Resolution of Identity](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/local_ri.html)
-   [Constrained DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/constrained.html)
-   [Constrained Nuclear-Electronic Orbital DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/cneo.html)
-   [Linear Scaling DFT](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/linear_scaling.html)
-   [GauXC](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/gauxc.html)

Density functional theory in CP2K is primarily provided by the Quickstep module. Most production calculations use the Gaussian and plane waves (GPW) method with Gaussian basis sets, pseudopotentials, and real-space grids for densities and potentials. The Gaussian augmented plane waves (GAPW) method extends the same framework to all-electron and more core-sensitive calculations.

For new inputs, first choose a consistent basis-set and potential pair, then converge the MGRID cutoffs and the SCF settings for the target property. The pages in this section collect the main Quickstep ingredients: GPW/GAPW, hybrid functionals and ADMM, local RI, constraints, k-points, basis sets, pseudopotentials, and grid convergence.

## References

-   [Kühne2020](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#kuhne2020)

-   [Iannuzzi2026](https://manual.cp2k.org/cp2k-2026_2-branch/bibliography.html#iannuzzi2026)
