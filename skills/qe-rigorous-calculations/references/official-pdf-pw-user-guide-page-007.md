# pw_user_guide.pdf — page 7

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `790b285b0dd793d63fc38d945833e508726e54046a6f88d420a5d1324939e9b2`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
The keywords may be followed on the same line by an option. Unknown fields are ignored. See
the files mentioned above for details on the available “cards”.
    Comments lines in “cards” can be introduced by either a “!” or a “#” character in the first
position of a line.
    Note about k-points: The k-point grid can be either automatically generated or manually
provided as a list of k-points and a weight in the Irreducible Brillouin Zone only of the Bravais
lattice of the crystal. The code will generate (unless instructed not to do so: see variable nosym)
all required k-points and weights if the symmetry of the system is lower than the symmetry of
the Bravais lattice. The automatic generation of k-points follows the convention of Monkhorst
and Pack.

3.2    Data files
The output data files are written in the directory outdir/prefix.save, as specified in variable
prefix (a string that is prepended to all file names, whose default value is prefix=’pwscf’).
outdir is specified via environment variable ESPRESSO TMPDIR. The usage of variable outdir
is still possible but deprecated. The FoX library is used to write a “head” data file in a XML
format. This file has a “schema” that can be found on https://github.com/QEF/qeschemas.
     In case of multi-step calculations such as: ’md’, ’relax’, ’vc-md ’, ’vc-relax’ the XML
files contains also elements reporting the intermediate configurations. By default includes a
maximum of 250 intermediate elements uniformly distributed along the trajectory and including
first and last step. If one want to change the maximum number of intermediate steps described
in the XML file it is sufficient to set the MAX XML STEPS variable to the desired value.
     For more information about the XML file contents see the Developer Manual. The data
directory contains binary files that are not guaranteed to be readable on different machines. If
you need file portability, compile the code with HDF5 (see the general User Guide).
     The execution stops if you create an “EXIT” file prefix.EXIT either in the working directory
(i.e. where the program is executed), or in the outdir directory. Note that with some versions
of MPI, the working directory is the directory where the executable is! The advantage of this
procedure is that all files are properly closed, whereas just killing the process may leave data
and output files in an unusable state. If you start the execution with the EXIT file already
in place, the code will stop after initialization. Alternatively: set nstep to 0 in input. This is
useful to have a quick check of the correctness of the input.

3.3    Electronic structure calculations
Single-point (fixed-ion) SCF calculation Set calculation=’scf’ (this is actually the
default). Namelists &IONS and &CELL will be ignored. For LSDA spin-polarized calculations
(that is: with a fixed quantization axis for magnetization), set nspin=2. Note that the number
of k-points will be internally doubled (one set of k-points for spin-up, one set for spin-down).
See example 1 (that is: PW/examples/example01).

Band structure calculation First perform a SCF calculation as above; then do a non-SCF
calculation (at fixed potential, computed in the previous step) with the desired k-point grid
and number nbnd of bands. Use calculation=’bands’ if you are interested in calculating only
the Kohn-Sham states for the given set of k-points (e.g. along symmetry lines: see for instance
http://www.cryst.ehu.es/cryst/get kvec.html). Specify instead calculation=’nscf’ if

                                                7
```
