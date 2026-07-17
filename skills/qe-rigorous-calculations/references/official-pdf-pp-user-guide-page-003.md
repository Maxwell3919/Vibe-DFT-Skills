# pp_user_guide.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pp_user_guide.pdf
- Retrieved: 2026-07-17T11:53:40+00:00
- Official source SHA-256: `8f53208b6cafea0d02640a33d25839f15ff9c8478702b435582b19f31f6b79fb`
- Extracted text SHA-256: `b1f2b6c49db896af89eccb2a16eba0cf6824c4f3c792758aa0172d9d66e262ba`
- Official Last-Modified: Mon, 08 Dec 2025 21:41:31 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
and
      P. Giannozzi, O. Andreussi, T. Brumme, O. Bunau, M. Buongiorno Nardelli, M.
      Calandra, R. Car, C. Cavazzoni, D. Ceresoli, M. Cococcioni, N. Colonna, I. Carn-
      imeo, A. Dal Corso, S. de Gironcoli, P. Delugas, R. A. DiStasio Jr, A. Ferretti, A.
      Floris, G. Fratesi, G. Fugallo, R. Gebauer, U. Gerstmann, F. Giustino, T. Gorni, J
      Jia, M. Kawamura, H.-Y. Ko, A. Kokalj, E. Küçükbenli, M .Lazzeri, M. Marsili, N.
      Marzari, F. Mauri, N. L. Nguyen, H.-V. Nguyen, A. Otero-de-la-Roza, L. Paulatto,
      S. Poncé, D. Rocca, R. Sabatini, B. Santra, M. Schlipf, A. P. Seitsonen, A. Smo-
      gunov, I. Timrov, T. Thonhauser, P. Umari, N. Vast, X. Wu, S. Baroni, J.Phys.:
      Condens.Matter 29, 465901 (2017)
    Users of the GPU-enabled version should also cite the following paper:
      P. Giannozzi, O. Baseggio, P. Bonfà, D. Brunato, R. Car, I. Carnimeo, C. Cavazzoni,
      S. de Gironcoli, P. Delugas, F. Ferrari Ruffino, A. Ferretti, N. Marzari, I. Timrov,
      A. Urru, S. Baroni, J. Chem. Phys. 152, 154105 (2020)
   Note the form Quantum ESPRESSO for textual citations of the code. Please also see
package-specific documentation for further recommended citations. Pseudopotentials should
be cited as (for instance)
      [ ] We used the pseudopotentials C.pbe-rrjkus.UPF and O.pbe-vbc.UPF from
      http://www.quantum-espresso.org.


3     Compilation
PostProc is part of the Quantum ESPRESSO distribution and depends upon PWscf for com-
pilation. For instruction on how to download and compile Quantum ESPRESSO, please refer
to the general Users’ Guide, available in file Doc/user guide.pdf under the main Quantum
ESPRESSO directory, or in web site http://www.quantum-espresso.org.
    Once Quantum ESPRESSO is correctly configured, PostProc can be compiled by just
typing make pp, from the main Quantum ESPRESSO directory; or typing make from the
PP/ subdirectory. Several executable codes are produced in PP/bin and linked to bin/.


4     Usage
All codes for which input documentation is not explicitly mentioned below have some documen-
tation in the header of the fortran sources. In the following, subdirectories containing examples
are found in PP/examples/; “Example N” stands for subdirectory PP/examples/exampleN/.
    All quantities whose dimensions are not explicitly specified are in RYDBERG ATOMIC
UNITS. Charge is ”number” charge (i.e. not multiplied by e); potentials are in energy units
(i.e. they are multiplied by e).

4.1    Plotting selected quantities
The main postprocessing code pp.x extracts the specified data from the data files produced by
PWscf (pw.x executable) or CP (cp.x executable); prepares data for plotting by writing them
into formats that can be read by several plotting programs.

                                               3
```
