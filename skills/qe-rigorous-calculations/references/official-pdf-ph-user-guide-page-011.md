# ph_user_guide.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `cf2070eb974240dc5423c0e686570dcb77e52a40b629cc772c02032e47d9796c`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Wrong degeneracy error in star q Verify the q-vector for which you are calculating
phonons. In order to check whether a symmetry operation belongs to the small group of q,
the code compares q and the rotated q, with an acceptance tolerance of 10−5 (set in routine
PW/src/eqvect.f90). You may run into trouble if your q-vector differs from a high-symmetry
point by an amount in that order of magnitude.

Mysterious symmetry-related errors Symmetry-related errors like symmetry operation
is non orthogonal, or Wrong representation, or Wrong degeneracy, are almost invariably a con-
sequence of atomic positions that are close to, but not sufficiently close to, symmetry positions.
If such errors occur, set the Bravais lattice using the correct ibrav value (i.e. do not use
ibrav=0), use Wyckoff positions if known. This must be done in the self-consistent calculation.


A       Appendix: Electron-phonon coefficients
The electron-phonon coefficients g are defined as
                                                     !1/2
                                           h̄                         dVSCF
                      gqν (k, i, j) =                       hψi,k |          · ˆqν |ψj,k+q i.   (1)
                                         2M ωqν                        dûqν
The phonon linewidth γqν is defined by
                               XZ       d3 k
                γqν = 2πωqν                  |gqν (k, i, j)|2 δ(eq,i − eF )δ(ek+q,j − eF ),      (2)
                               ij       ΩBZ

while the electron-phonon coupling constant λqν for mode ν at wavevector q is defined as
                                               γqν
                                     λqν =            2
                                                                                         (3)
                                           πh̄N (eF )ωqν
where N (eF ) is the DOS at the Fermi level. The spectral function is defined as
                                              1                      γqν
                            α2 F (ω) =
                                                     X
                                                        δ(ω − ωqν )       .                      (4)
                                           2πN (eF ) qν             h̄ωqν
The electron-phonon mass enhancement parameter λ can also be defined as the first reciprocal
momentum of the spectral function:
                                          X                 Z
                                                                α2 F (ω)
                                    λ=          λqν = 2                  dω.                     (5)
                                           qν                      ω

    Note that a factor M −1/2 is hidden in the definition of normal modes as used in the code.
    McMillan:                                "                     #
                                    ΘD            −1.04(1 + λ)
                              Tc =       exp                                                (6)
                                    1.45       λ(1 − 0.62µ∗ ) − µ∗
or (better?)                                         "                            #
                                     ωlog        −1.04(1 + λ)
                                Tc =      exp                                                    (7)
                                     1.2      λ(1 − 0.62µ∗ ) − µ∗
where                                            "                              #
                                            2 Z dω 2
                                 ωlog = exp       α F (ω)logω                                    (8)
                                            λ   ω

                                                         11
```
