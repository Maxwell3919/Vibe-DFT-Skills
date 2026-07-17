# Hubbard_input.pdf — page 1

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `e82c3023f59a764074c1889768c9a628eec541ba09763b040db4d2b4bb47f1bc`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
          New DFT+Hubbard input in
      Quantum ESPRESSO (since v.7.3.1)

                                   December 8, 2025


Contents
1 History                                                                                  1

2 Why changing the old input?                                                              2

3 New DFT+Hubbard input                                                                  2
  3.1 DFT+U (Dudarev’s formulation) . . . . . . . . . . . . . . . . . . . . . . . . . . 2
  3.2 DFT+U +J (Liechtenstein’s formulation) . . . . . . . . . . . . . . . . . . . . . . 9
  3.3 DFT+U +V (Dudarev’s formulation) . . . . . . . . . . . . . . . . . . . . . . . . 11

4 Calculation of Hubbard parameters                                                       15

5 Pseudopotentials                                                                        16

6 Noncollinear DFT+Hubbard                                                                16


1    History
Density-functional theory (DFT) with the on-site Hubbard U correction (DFT+U ) was im-
plemented in Quantum ESPRESSO since the early days of the Quantum ESPRESSO
project (early 2000’s). In the literature, this method used to be called (and still often is)
as “LDA+U ”, since in the original paper that first introduced this method the local density
approximation (LDA) for the exchange-correlation functional was used [1]. However, other
functionals other than LDA can be used with the Hubbard correction, and hence we obtain
e.g. GGA+U , SCAN+U , etc. Therefore, it might be confusing to continue using the old name
“LDA+U ”. Instead, for the sake of generality it is better to use a generic name “DFT+U ” and
then specify which functional is used.
    In 1995 Liechtenstein and coworkers introduced a formulation of the Hubbard-corrected
DFT that includes not only the Hubbard U correction but also the Hund J correction [2].
Sometimes in is called in the literature as DFT+U +J. Within this formulation it is possible
to set J = 0 and thus obtain DFT+U .




                                             1
```
