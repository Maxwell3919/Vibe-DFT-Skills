# Hubbard_input.pdf — page 17

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `e8619be60d7b212e045ab7cb1fa243d8568fefb59a50ddad7ed3376482e3eb41`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
the electronic structure for a given atom in the Periodic table and what atomic orbitals were
included in the valence region.


6      Noncollinear DFT+Hubbard
The Dudarev’s formulation of DFT+U and DFT+U +V has been extended to the noncollinear
framework [24] starting from Quantum ESPRESSO v7.3. This includes also the calculation
of Hubbard forces and Hubbard stresses by pw.x. Moreover, the calculation of Hubbard U
and V parameters using the HP code has been also extended to the noncollinear Dudarev’s
framework.
   Therefore, now in Quantum ESPRESSO there are two noncollinear implementations of
DFT+U :
      Dudarev’s framework (lda plus u kind=0)

      Liechtenstein’s framework (lda plus u kind=1)
How to activate these frameworks? Note, when J = 0 these two frameworks are equivalent. If
J is not specified in the input, then the Dudarev’s formulation is activated. If instead (nonzero)
J is specified in the input, then the Liechtenstein’s framework is activated. This is true also
for the collinear and non-spinpolarized case.
    Noncollinear DFT+U +V is available only in the Dudarev’s formulation.


References
    [1] V.I. Anisimov, J. Zaanen, and O.K. Andersen, Band theory and Mott insulators: Hubbard
        U instead of Stoner I, Phys. Rev. B. 44, 943 (1991).

    [2] A.I. Liechtenstein, V.I. Anisimov, J. Zaanen, Density-functional theory and strong inter-
        actions: Orbital ordering in Mott-Hubbard insulators, Phys. Rev. B 52, R5467 (1995).

    [3] S.L. Dudarev, G.A. Botton, S.Y. Savrasov, C.J. Humphreys, A.P. Sutton, Electron-
        energy-loss spectra and the structural stability of nickel oxide: An LSDA+U study, Phys.
        Rev. B 57, 1505 (1998).

    [4] B. Himmetoglu, R.M. Wentzcovitch, M. Cococcioni, First-principles study of electronic
        and structural properties of CuO, Phys. Rev. B 84, 115108 (2011).

    [5] A. Bajaj, J.P. Janet, and H.J. Kulik, Communication: Recovering the flat-plane condition
        in electronic structure theory at semi-local DFT cost, J. Chem. Phys. 147, 191101 (2017).

    [6] E.B. Linscott, D.J. Cole, M.C. Payne, and D.D. O’Regan, Role of spin in the calculation
        of Hubbard U and Hund’s J parameters from first principles, Phys. Rev. B 98, 235157
        (2018).

    [7] G. Racah, Theory of Complex Spectra. I, Phys. Rev. 61, 186 (1942).

    [8] G. Racah, Theory of Complex Spectra. II, Phys. Rev. 62, 438 (1942).

    [9] G. Racah, Theory of Complex Spectra. III, Phys. Rev. 63, 367 (1943).

                                                17
```
