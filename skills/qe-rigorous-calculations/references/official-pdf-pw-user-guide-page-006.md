# pw_user_guide.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `6ccdb9585a7093b78b81a2f72484767f0e9999a30ab591f83b8cb30561ec5658`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3     Using PWscf
Input files for pw.x may be either written by hand or produced via the PWgui graphical interface
by Anton Kokalj, included in the Quantum ESPRESSO distribution. See PWgui-x.y.z/INSTALL
(where x.y.z is the version number) for more info on PWgui, or GUI/README if you are using
sources from the repository.
   You may take the tests (in test-suite/) and examples (in PW/examples/) distributed
with Quantum ESPRESSO as templates for writing your own input files. You may find
input files (typically with names ending with .in) either in test-suite/pw */ or in the vari-
ous PW/examples/*/results/ subdirectories, after you have run the examples. All examples
contain a README file.

3.1    Input data
Input data is organized as several namelists, followed by other fields (“cards”) introduced by
keywords. The namelists are
     &CONTROL:             general variables controlling the run
     &SYSTEM:              structural information on the system under investigation
     &ELECTRONS:           electronic variables: self-consistency, smearing
     &IONS (optional): ionic variables: relaxation, dynamics
     &CELL (optional): variable-cell optimization or dynamics
Optional namelist may be omitted if the calculation to be performed does not require them.
This depends on the value of variable calculation in namelist &CONTROL. Most variables
in namelists have default values. Only the following variables in &SYSTEM must always be
specified:
     nat        (integer) number of atoms in the unit cell
     ntyp       (integer) number of types of atoms in the unit cell
     ecutwfc (real)        kinetic energy cutoff (Ry) for wavefunctions.
                                                                   ibrav    (integer)          Bravais-l
plus the variables needed to describe the crystal structure, e.g.:
                                                                   celldm (real, dimension 6) crystallo
Alternative ways to input structural data are described in files PW/Doc/INPUT PW.*. For metal-
lic systems, you have to specify how metallicity is treated in variable occupations. If you
choose occupations=’smearing’, you have to specify the smearing type smearing and the
smearing width degauss. Spin-polarized systems are as a rule treated as metallic system,
unless the total magnetization, tot magnetization is set to a fixed value, or if occupation
numbers are fixed (occupations=’from input’ and card OCCUPATIONS).
    Detailed explanations of the meaning of all variables are found in files PW/Doc/INPUT PW.*.
Almost all variables have default values, which may or may not fit your needs.
    Comment lines in namelists can be introduced by a ”!”, exactly as in fortran code.
    After the namelists, you have several fields (“cards”) introduced by keywords with self-
explanatory names:

      ATOMIC SPECIES
      ATOMIC POSITIONS
      K POINTS
      CELL PARAMETERS (optional)
      OCCUPATIONS (optional)


                                               6
```
