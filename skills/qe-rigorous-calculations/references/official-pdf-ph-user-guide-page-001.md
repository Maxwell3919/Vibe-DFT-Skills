# ph_user_guide.pdf — page 1

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `65c3cf235d6ae019282ee6e5bc6fce449da92168e25c6a6a0f160ce3cd342608`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
                   PHonon User’s Guide (v. 7.4)


Contents
1 Introduction                                                                                  1

2 People                                                                                        1

3 Installation                                                                                  2
  3.1 Structure of the PHonon package . . . . . . . . . . . . . . . . . . . . . . . . . . .     3
  3.2 Compilation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   3

4 Using PHonon                                                                                 4
  4.1 Single-q calculation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
  4.2 Calculation of interatomic force constants in real space . . . . . . . . . . . . . . 5
  4.3 Calculation of electron-phonon interaction coefficients . . . . . . . . . . . . . . . 5
  4.4 DFPT with the tetrahedron method . . . . . . . . . . . . . . . . . . . . . . . . . 6
  4.5 Calculation of electron-phonon interaction coefficients with the tetrahedron method 6
  4.6 Phonons for two-dimensional crystals . . . . . . . . . . . . . . . . . . . . . . . . 7
  4.7 Phonons from DFPT+U . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
  4.8 Fourier interpolation of phonon potential . . . . . . . . . . . . . . . . . . . . . . 7
  4.9 Calculation of phonon-renormalization of electron bands . . . . . . . . . . . . . 8

5 Parallelism                                                                                   8

6 Troubleshooting                                                                                9

A Appendix: Electron-phonon coefficients                                                        10


1    Introduction
This guide covers the usage of the PHonon package for linear-response calculations.
    It is also assumed that you know the physics behind Quantum ESPRESSO, the methods
it implements, and in particular the physics and the methods of PHonon. It also assumes that
you have already installed, or know how to install, Quantum ESPRESSO. If not, please read
the general User’s Guide for Quantum ESPRESSO, found in subdirectory Doc/ of the main
Quantum ESPRESSO directory, or consult the web site http://www.quantum-espresso.org.

                                                1
```
