# user_guide.pdf — page 19

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `5ccd31d972d659c8797bae9ac3e7659c362a683912f026a6fb7836c70a6674da`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Other functionals. Besides exchange ( x), correlation ( c) and exchange plus correlation
( xc), a fourth kind of functionals is available in libxc, the kinetic functionals ( k). At present,
they are not usable in Quantum ESPRESSO.

2.6.5   XC test
A testing program, xclib test.x, for the XClib library of Quantum ESPRESSO is available.
The program is available for LDA, GGA and MGGA functionals (both QE and Libxc). It also
tests the potential derivatives for LDA (dmxc) and GGA (dgcxc).
Another small program, xc infos.x, is available in the XClib folder starting from v6.8. It
receives as input the name of any DFT usable in Quantum ESPRESSO (both internal and
libxc) and provides infos about their family, type, external parameters, limitations, references,
etc.
See XClib/README.TEST file for further details on each of the two programs.

2.7     Compilation
The compiled codes can run with any input: almost all variables are dinamically allocated at
run time. Only a few variables have fixed dimensions, set in file Modules/parameters.f90:

        ntypx = 10,     &! max number of different types of atom
        npsx   = ntypx, &! max number of different PPs (obsolete)
        nsx    = ntypx, &! max number of atomic species (CP)
        npk    = 40000, &! max number of k-points
        lmaxx = 4,       &! max non local angular momentum (l=0 to lmaxx)
        lqmax= 2*lmaxx+1 ! max number of angular momenta of Q

These values should work for the vast majority of cases. In case you need more atomic types
or more k-points, edit this file and recompile.
    At your choice, you may compile the complete Quantum ESPRESSO suite of programs
(with make all), or only some specific programs. All executables are linked in main bin
directory. make with no arguments yields ain updated list of valid compilation targets.
    For the setup of the GUI, refer to the PWgui-X.Y.Z /INSTALL file, where X.Y.Z stands for
the version number of the GUI (should be the same as the general version number). If you are
using sources from the git repository, see the GUI/README file instead.
    If make refuses for some reason to download additional packages, manually download them
into subdirectory archive/, not unpacking or uncompressing them, and try make again. Also
see Sec.(2.1).

2.8     Running tests and examples
As a final check that compilation was successful, you may want to run some or all of the tests
and examples. Notice that most tests and examples are devised to be run serially or on a small
number of processors; do not use tests and examples to benchmark parallelism, do not try to
run on too many processors.




                                                19
```
