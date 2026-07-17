# ph_user_guide.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `030cba416019bff3b002ec7cf848f720c288b09bbf9817ba12b3e3bf48e52b06`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    Users of the GPU-enabled version should also cite the following paper:

      P. Giannozzi, O. Baseggio, P. Bonfà, D. Brunato, R. Car, I. Carnimeo, C. Cavazzoni,
      S. de Gironcoli, P. Delugas, F. Ferrari Ruffino, A. Ferretti, N. Marzari, I. Timrov,
      A. Urru, S. Baroni, J. Chem. Phys. 152, 154105 (2020)

   Note the form Quantum ESPRESSO for textual citations of the code. Please also see
package-specific documentation for further recommended citations. Pseudopotentials should
be cited as (for instance)

      [ ] We used the pseudopotentials C.pbe-rrjkus.UPF and O.pbe-vbc.UPF from
      http://www.quantum-espresso.org.


3     Installation
PHonon is a Quantum ESPRESSO package and it is tightly bound to Quantum ESPRESSO.
For instruction on how to download and compile Quantum ESPRESSO, please refer to
the general Users’ Guide, available in file Doc/user guide.pdf under the main Quantum
ESPRESSO directory, or in web site http://www.quantum-espresso.org.
   Once Quantum ESPRESSO is correctly configured, PHonon is compiled by just typing
make ph, from the main Quantum ESPRESSO directory; or, if you use CMake, by just
typing make.

3.1    Structure of the PHonon package
PHonon has the following directory structure, contained in a subdirectory PHonon/ of the main
Quantum ESPRESSO tree:
     Doc/        : contains the user guide and input data description
     examples/ : some running examples
     PH/         : source files for phonon calculations and analysis
     Gamma/      : source files for Gamma-only phonon calculation
     FD/         : source files for FInite-Difference calculations
Important Notice: since v.5.4, many modules and routines that were common to all linear-
response Quantum ESPRESSO codes are moved into the new LR Modules subdirectory
of the main tree. Since v.6.0, the D3 code for anharmonic force constant calculations has
been superseded by the D3Q code, available on https://sourceforge.net/projects/d3q/
and automatically downloadable from Quantum ESPRESSO.
    The codes available in the PHonon package can perform the following types of calculations:

     phonon frequencies and eigenvectors at a generic wave vector, using Density-Functional
      Perturbation Theory;

     effective charges and dielectric tensors;

     electron-phonon interaction coefficients for metals;

     interatomic force constants in real space;

     Infrared and Raman (nonresonant) cross section.

                                                  3
```
