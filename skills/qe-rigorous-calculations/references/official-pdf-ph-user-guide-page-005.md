# ph_user_guide.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `a23402cf6c58477e6a6973cb0249add07588c0236e96af0fd1a749dbcc525b6f`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    The main code ph.x can be used whenever PWscf can be used, with the exceptions of hybrid
and meta-GGA functionals, external electric fields, constraints on magnetization, nonperiodic
boundary conditions. USPP and PAW are not implemented for higher-order response calcula-
tions. See the header of file PHonon/PH/phonon.f90 for a complete and updated list of what
PHonon can and cannot do.
    Since version 4.0 it is possible to safely stop execution of ph.x code using the same mecha-
nism of the pw.x code, i.e. by creating a file prefix.EXIT in the working directory. Execution
can be resumed by setting recover=.true. in the subsequent input data. Moreover the exe-
cution can be (cleanly) stopped after a given time is elapsed, using variable max seconds. See
example/Recover example/.

4.1    Single-q calculation
The phonon code ph.x calculates normal modes at a given q-vector, starting from data files
produced by pw.x with a simple SCF calculation. NOTE: the alternative procedure in which a
band-structure calculation with calculation=’phonon’ was performed as an intermediate step
is no longer implemented since version 4.1. It is also no longer needed to specify lnscf=.true.
for q 6= 0.
    The output data files appear in the directory specified by the variable outdir, with names
specified by the variable prefix. After the output file(s) has been produced (do not remove
any of the files, unless you know which are used and which are not), you can run ph.x.
    The first input line of ph.x is a job identifier. At the second line the namelist &INPUTPH
starts. The meaning of the variables in the namelist (most of them having a default value) is
described in file Doc/INPUT PH.*. Variables outdir and prefix must be the same as in the
input data of pw.x. Presently you can specify amass(i) (a real variable) the atomic mass of
atomic type i or you can use the default one deduced from the periodic table on the basis of
the element name. If amass(i) is not given as input of ph.x, the one given as input in pw.x is
used. When this is 0 the default one is used.
    After the namelist you must specify the q-vector of the phonon mode, in Cartesian coordi-
nates and in units of 2π/a.
    Notice that the dynamical matrix calculated by ph.x at q = 0 does not contain the non-
analytic term occurring in polar materials, i.e. there is no LO-TO splitting in insulators.
Moreover no Acoustic Sum Rule (ASR) is applied. In order to have the complete dynamical
matrix at q = 0 including the non-analytic terms, you need to calculate effective charges by
specifying option epsil=.true. to ph.x. This is however not possible (because not physical!)
for metals (i.e. any system subject to a broadening).
    At q = 0, use program dynmat.x to calculate the correct LO-TO splitting, IR cross sections,
and to impose various forms of ASR. If ph.x was instructed to calculate Raman coefficients,
dynmat.x will also calculate Raman cross sections for a typical experimental setup. Input
documentation in the header of PHonon/PH/dynmat.f90.
    See Example 01 for a simple phonon calculations in Si, Example 06 for fully-relativistic
calculations (LDA) on Pt, Example 07 for fully-relativistic GGA calculations.

4.2    Calculation of interatomic force constants in real space
First, dynamical matrices are calculated and saved for a suitable uniform grid of q-vectors
(only those in the Irreducible Brillouin Zone of the crystal are needed). Although this can be

                                               5
```
