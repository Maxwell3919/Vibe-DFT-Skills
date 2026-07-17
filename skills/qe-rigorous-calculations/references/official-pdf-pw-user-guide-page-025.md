# pw_user_guide.pdf — page 25

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `22663e10373a8d590345329af76ab18718f47b84f24f38877a3eb316ecfadc35`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   Note that in parallel execution, it is very convenient to have FFT grid dimensions along z
that are a multiple of the number of processors.

pw.x does not find all the symmetries you expected pw.x determines first the symmetry
operations (rotations) of the Bravais lattice; then checks which of these are symmetry operations
of the system (including if needed fractional translations). This is done by rotating (and
translating if needed) the atoms in the unit cell and verifying if the rotated unit cell coincides
with the original one.
    Assuming that your coordinates are correct (please carefully check!), you may not find all
the symmetries you expect because:

    the number of significant figures in the atomic positions is not large enough. In file
     PW/src/eqvect.f90, the variable accep is used to decide whether a rotation is a sym-
     metry operation. Its current value (10−5 ), set in module PW/src/symm base.f90, is quite
     strict: a rotated atom must coincide with another atom to 5 significant digits. You may
     change the value of accep and recompile.

    they are not acceptable symmetry operations of the Bravais lattice. This is the case
     for C60 , for instance: the Ih icosahedral group of C60 contains 5-fold rotations that are
     incompatible with translation symmetry.

    the system is rotated with respect to symmetry axis. For instance: a C60 molecule in the
     fcc lattice will have 24 symmetry operations (Th group) only if the double bond is aligned
     along one of the crystal axis; if C60 is rotated in some arbitrary way, pw.x may not find
     any symmetry, apart from inversion.

    they contain a fractional translation that is incompatible with the FFT grid (see next
     paragraph). Note that if you change cutoff or unit cell volume, the automatically com-
     puted FFT grid changes, and this may explain changes in symmetry (and in the number
     of k-points as a consequence) for no apparent good reason (only if you have fractional
     translations in the system, though).

    a fractional translation, without rotation, is a symmetry operation of the system. This
     means that the cell is actually a supercell. In this case, all symmetry operations containing
     fractional translations are disabled. The reason is that in this rather exotic case there is no
     simple way to select those symmetry operations forming a true group, in the mathematical
     sense of the term.

Self-consistency is slow or does not converge at all Bad input data will often result in
bad scf convergence. Please carefully check your structure first, e.g. using XCrySDen.
   Assuming that your input data is sensible :

  1. Verify if your system is metallic or is close to a metallic state, especially if you have few
     k-points. If the highest occupied and lowest unoccupied state(s) keep exchanging place
     during self-consistency, forget about reaching convergence. A typical sign of such behavior
     is that the self-consistency error goes down, down, down, than all of a sudden up again,
     and so on. Usually one can solve the problem by adding a few empty bands and a small
     broadening.


                                                25
```
