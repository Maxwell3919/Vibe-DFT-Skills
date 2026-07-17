# plumed_quick_ref.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `4302b11f23c4afd8d73d69f3bc771010ed7ab9a0db2fcd20356827f3747d0070`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
1      Introduction
PLUMED[1] is a plugin for free energy calculation in molecular systems which works
together with some of the most popular molecular dynamics engines, including clas-
sical (GROMACS, NAMD, DL POLY, AMBER and LAMMPS), GPU-accelerated
(ACEMD) and ab-initio (Quantum ESPRESSO) codes.
    Free energy calculations can be performed as a function of many order parameters
with a particular focus on biological problems using state of the art methods such as
metadynamics[2], umbrella sampling and Jarzynski-equation based steered MD.
    The software, written in ANSI-C language, can be easily interfaced with both for-
tran and C/C++ codes.
    The PLUMED user guide can be downloaded here
    https://sites.google.com/site/plumedweb/documentation
    and PLUMED tutorial can be found here
    http://sites.google.com/site/plumedtutorial2010/.

     All the features in PLUMED are compatible with Quantum ESPRESSO but:

     • variable cell calculations

     • non-orthorhombic cell

     • energy related collective variables

1.1     Overview
A system described by a set of coordinates x and a potential V (x) evolving under
the action of a dynamics whose equilibrium distribution is canonical at a temperature
T . We explore the properties of the system as a function of a finite number of CVs
Sα (x), α = 1, d. The equilibrium behavior of these variables is defined by the
probability distribution

                                          exp(−(1/T )F (s))
                             P (s) = R                                                (1)
                                          ds exp(−(1/T )F (s))
     where s denotes the d dimensional vector (s1 , ..., sd ) and the free energy is given
by
                                     Z
                                                 1
                     F (s) = T ln(       dx exp(− V (x)) δ(s − S(x)))                 (2)
                                                 T
    Here capital S is used for denoting the function of the coordinates S(x), while lower
case s is used for denoting the value of the CVs.
    In metadynamics the free energy is reconstructed recursively, starting from the
bottom of the well by a history-dependent random walk that explores a larger and
larger portion of configuration space. A small repulsive Gaussian potential is added




                                              2
```
