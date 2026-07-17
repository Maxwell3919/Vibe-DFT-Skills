# pw_user_guide.pdf — page 27

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `55d01194a76d08be29c1651d0905290439cd822e8c57efebb10fcc128285f8cf`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
default thresholds ( etot conv thr and forc conv thr ) in 15-25 BFGS steps (depending on the
starting configuration). This may not happen when your system is characterized by ”floppy”
low-energy modes, that make very difficult (and of little use anyway) to reach a well converged
structure, no matter what. Other possible reasons for a problematic convergence are listed
below.
    Close to convergence the self-consistency error in forces may become large with respect to
the value of forces. The resulting mismatch between forces and energies may confuse the line
minimization algorithm, which assumes consistency between the two. The code reduces the
starting self-consistency threshold conv thr when approaching the minimum energy configura-
tion, up to a factor defined by upscale. Reducing conv thr (or increasing upscale) yields a
smoother structural optimization, but if conv thr becomes too small, electronic self-consistency
may not converge. You may also increase variables etot conv thr and forc conv thr that
determine the threshold for convergence (the default values are quite strict).
    A limitation to the accuracy of forces comes from the absence of perfect translational in-
variance. If we had only the Hartree potential, our PW calculation would be translationally
invariant to machine precision. The presence of an XC potential introduces Fourier components
in the potential that are not in our basis set. This loss of precision (more serious for gradient-
corrected functionals) translates into a slight but detectable loss of translational invariance (the
energy changes if all atoms are displaced by the same quantity, not commensurate with the
FFT grid). This sets a limit to the accuracy of forces. The situation improves somewhat by
increasing the ecutrho cutoff.

pw.x stops during variable-cell optimization in checkallsym with non orthogonal
operation error Variable-cell optimization may occasionally break the starting symmetry of
the cell. When this happens, the run is stopped because the number of k-points calculated for
the starting configuration may no longer be suitable. Possible solutions:

    start with a nonsymmetric cell;

    use a symmetry-conserving algorithm: the Wentzcovitch algorithm (cell dynamics=’damp-w’)
     should not break the symmetry.




                                                27
```
