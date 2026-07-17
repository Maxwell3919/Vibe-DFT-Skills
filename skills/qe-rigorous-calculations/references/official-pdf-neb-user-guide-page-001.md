# neb_user_guide.pdf — page 1

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/neb_user_guide.pdf
- Retrieved: 2026-07-17T11:53:27+00:00
- Official source SHA-256: `acc9df963f4b8009b54b8f253bf207386ed0fd2793881764886022af09c58d2a`
- Extracted text SHA-256: `9713fe411f7b20185ad5d0a21635631ac1330fedeb827848a21a82082f4d2f48`
- Official Last-Modified: Mon, 08 Dec 2025 21:37:56 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
                   PWneb User’s Guide (v. 7.4)


Contents
1 Introduction                                                                                     1

2 People and terms of use                                                                          1

3 Compilation                                                                                      2
  3.1 Running examples       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   3

4 Parallelism                                                                                      3

5 Using PWneb                                                                                      3

6 Performances                                                                                     6

7 Troubleshooting                                                                                  6


1    Introduction
This guide covers the usage of PWneb, version 7.4: an open-source package for the calculation
of energy barriers and reaction pathway using the Nudged Elastic Band (NEB) method.
    This guide assumes that you know the physics that PWneb describes and the methods it
implements. It also assumes that you have already installed, or know how to install, Quantum
ESPRESSO. If not, please read the general User’s Guide for Quantum ESPRESSO, found
in subdirectory Doc/ of the main Quantum ESPRESSO directory, or consult the web site:
http://www.quantum-espresso.org.
    PWneb is part of the Quantum ESPRESSO distribution and uses the PWscf package as
electronic-structure computing tools (“engine”). It is however written in a modular way and
could be adapted to use other codes as “engine”. Since v.4.3 the NEB calculation is performed
by a separate executable neb.x and no longer by pw.x. Also note that NEB with Car-Parrinello
molecular dynamics is no longer implemented since v.4.3.




                                                1
```
