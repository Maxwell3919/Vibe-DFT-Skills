# pw_user_guide.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `40b75f2ce3567f465eb6fb0a89e83e7ad698a48dc680e940c6c11fed3c9ad61d`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   Note the form Quantum ESPRESSO for textual citations of the code. Please also see
package-specific documentation for further recommended citations. Pseudopotentials should
be cited as (for instance)

      [ ] We used the pseudopotentials C.pbe-rrjkus.UPF and O.pbe-vbc.UPF from
      http://www.quantum-espresso.org.

    References for all exchange-correlation functionals can be found inside file Modules/funct.f90.


2     Compilation
PWscf is included in the core Quantum ESPRESSO distribution. Instruction on how to in-
stall it can be found in the general documentation (User’s Guide) for Quantum ESPRESSO.
    Typing make pw from the main Quantum ESPRESSO directory or make from the PW/
subdirectory produces the pw.x executable in PW/src and a link to the bin/ directory. In
addition, the following utility programs, and related links in bin/, are produced in PW/src:

     dist.x symbolic link to pw.x: reads input data for PWscf, calculates distances and angles
      between atoms in a cell, taking into account periodicity,

and in PW/tools:

     ev.x fits energy-vs-volume data to an equation of state

     kpoints.x produces lists of k-points

     ibrav2cell.x and cell2ibrav.x convert from variables used in Quantum ESPRESSO
      to specify the unit cell to primitive lattice translations, and vice versa

     scan ibrav.x works as cell2ibrav.x but tries to figure out whether the axis are rotated
      with respect to those assumed by Quantum ESPRESSO

     pwi2xsf.sh, pwo2xsf.sh process respectively input and output files (not data files!) for
      pw.x and neb.x (the latter, courtesy of Pietro Bonfà) and produce an XSF-formatted file
      suitable for plotting with XCrySDen: http://www.xcrysden.org/, a powerful crystalline
      and molecular structure visualization program. BEWARE: the pwi2xsf.sh shell script
      requires the pwi2xsf.x executables to be located somewhere in your PATH.

     cif2qe.sh: script converting from CIF (Crystallographic Information File) to a format
      suitable for Quantum ESPRESSO. Courtesy of Carlo Nervi (Univ. Torino, Italy).

The other auxiliary codes contain their own documentation in the source files.




                                               5
```
