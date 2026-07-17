# plumed_quick_ref.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `9ecd843a3f8d299c84c9ba11071f85722271fbe26a282dd49e99ba5c01d3a1f6`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    • They should clearly distinguish between the initial state, the final state and the
      intermediates.
    • They should describe all the slow events that are relevant to the process of inter-
      est.
    • Their number should not be too large, otherwise it will take a very long time to
      fill the free energy surface.

    If the free energy grows ’smoothly’ it is likely that the set of variables is complete.

    CVs compatible with Quantum ESPRESSO are, for instance:

    • Geometry-related variables. Such as distances, angles and dihedrals formed by
      atoms or groups of atoms. These variables are frequently used in the study of
      chemical reactions and biophysical systems.
    • Coordination numbers. It can be used to detect the presence of a bond between
      two atoms or for counting the bonds between two different atomic species.

    For a complete list of CVs implemented in PLUMED, please have a look at the PLUMED
reference manual. Energy related CVs are not compatible with Quantum
ESPRESSO.


2     Step-by-step metadynamics calculations
2.1    Compile Quantum ESPRESSO with PLUMED plugin
In this section, we will show how to compile Quantum ESPRESSO with PLUMED
plugin. First of all, one of the following versions of the source package has to be
downloaded:

    • Quantum ESPRESSO release 4.3 (http://qe-forge.org/gf/project/q-e), follow
      link ”Files” on the left)
    • SVN version (link as above, follow link ”SVN” on the left)

    To install Quantum ESPRESSO from source, you need first of all a minimal Unix
environment: basically, a command shell (e.g., bash or tcsh) and the utilities make,
awk, sed. Second, you need C and Fortran-95 compilers. For parallel execution, you
will also need MPI libraries and a “parallel” (i.e. MPI-aware) compiler. For massively
parallel machines, or for simple multicore parallelization, an OpenMP-aware compiler
and libraries are also required.[4].
    Then you need to run the configure script as usual. After the successful con-
figuration, just type make plumed. make plumed just untar PLUMED-latest.tar.gz,
move to PLUMED directory just under espresso, patch PW and CPV files and recompile
PW, CPV and clib. Please note that, do not try make all, that will compile the code
without the PLUMED plugin.
    Instructions for the impatient:

                                             4
```
