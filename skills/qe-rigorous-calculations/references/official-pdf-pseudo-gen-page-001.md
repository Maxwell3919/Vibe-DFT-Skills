# pseudo-gen.pdf — page 1

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `feaf834f90cd3ab6e42dc273d2a86935cf21432f3a47e962ae8880b98298ff06`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
              Notes on pseudopotential generation
                           Paolo Giannozzi
                          Università di Udine
             URL: http://www.fisica.uniud.it/∼giannozz
                                 February 28, 2019


Contents
1 Introduction                                                                          1
  1.1 Who needs to generate a pseudopotential? . . . . . . . . . . . . . . . .          1
  1.2 About similar work . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      2
  1.3 Pseudopotential generation, in general . . . . . . . . . . . . . . . . . .        2

2 Step-by-step Pseudopotential generation                                                3
  2.1 Choosing the generation parameters . . . . . . . . . . . . . . . . . . . .         3
      2.1.1 Exchange-correlation functional . . . . . . . . . . . . . . . . . .          3
      2.1.2 Valence-core partition . . . . . . . . . . . . . . . . . . . . . . .         4
      2.1.3 Electronic reference configuration . . . . . . . . . . . . . . . . .         5
      2.1.4 Nonlinear core correction . . . . . . . . . . . . . . . . . . . . . .        6
  2.2 Type of pseudization . . . . . . . . . . . . . . . . . . . . . . . . . . . .       7
      2.2.1 Pseudization energies . . . . . . . . . . . . . . . . . . . . . . . .        7
      2.2.2 Pseudization radii . . . . . . . . . . . . . . . . . . . . . . . . . .       8
      2.2.3 Choosing the local potential . . . . . . . . . . . . . . . . . . . .         8
  2.3 Generating the pseudopotential . . . . . . . . . . . . . . . . . . . . . .         9
  2.4 Checking for transferability . . . . . . . . . . . . . . . . . . . . . . . .      10

3 A worked example: Ti                                                                  10
  3.1 Single-projector, norm-conserving, no semicore . . . . . . . . . . . . . .        11
      3.1.1 Generation . . . . . . . . . . . . . . . . . . . . . . . . . . . . .        11
      3.1.2 Testing . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .     15
  3.2 Single-projector, norm-conserving, with semicore states . . . . . . . . .         19
  3.3 Testing in molecules and solids . . . . . . . . . . . . . . . . . . . . . .       22

A Atomic Calculations                                                                   22
  A.1 Nonrelativistic case . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    22
      A.1.1 Useful formulae . . . . . . . . . . . . . . . . . . . . . . . . . . .       23
  A.2 Fully relativistic case . . . . . . . . . . . . . . . . . . . . . . . . . . . .   23
  A.3 Scalar-relativistic case . . . . . . . . . . . . . . . . . . . . . . . . . . .    23
  A.4 Numerical solution . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      24

                                            1
```
