# user_guide.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `198ce64fdc0968c8ffcecdf24c821b0de845b9a95745eaad58d8b01b36270244`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    2.7   Compilation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   18
    2.8   Running tests and examples . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      18
          2.8.1 Test-suite . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    19
          2.8.2 Examples . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      19
    2.9   Installation tricks and problems . . . . . . . . . . . . . . . . . . . . . . . . . . .    20
          2.9.1 All architectures . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .     20
          2.9.2 Linux PC’s . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      21
          2.9.3 Linux PC clusters with MPI . . . . . . . . . . . . . . . . . . . . . . . . .        22
          2.9.4 Microsoft Windows . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       22
          2.9.5 Mac OS . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      23
          2.9.6 Cray machines . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       24

3 Parallelism                                                                                       25
  3.1 Understanding Parallelism . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .         25
  3.2 Running on parallel machines . . . . . . . . . . . . . . . . . . . . . . . . . . . .          25
  3.3 Parallelization levels . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      26
  3.4 Understanding parallel I/O . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .        27
  3.5 Tricks and problems . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .         28


1     Introduction
This guide gives a very general overview of Quantum ESPRESSO (opEn-Source Package for
Research in Electronic Structure, Simulation, and Optimization), version 7.5.0, and explains
how to build it from sources.
    The Quantum ESPRESSO distribution contains the core packages PWscf (Plane-Wave
Self-Consistent Field) and CP (Car-Parrinello) for the calculation of electronic-structure prop-
erties within Density-Functional Theory (DFT), using a Plane-Wave (PW) basis set and pseu-
dopotentials. It also includes other packages for more specialized calculations:

    • PWneb: energy barriers and reaction pathways through the Nudged Elastic Band (NEB)
      method.

    • PHonon: vibrational properties with Density-Functional Perturbation Theory (DFPT).

    • PostProc: codes and utilities for data postprocessing.

    • PWcond: ballistic conductance.

    • XSPECTRA: K-, L1 -, L2,3 -edge X-ray absorption spectra.

    • TD-DFPT: spectra from Time-Dependent Density-Functional Perturbation Theory.

    • GWL: electronic excitations within the GW approximation and with the Bethe-Salpeter
      Equation

    • EPW: calculation of the electron-phonon coefficients, carrier transport, phonon-limited
      superconductivity and phonon-assisted optical processes;

    • HP: calculation of Hubbard U parameters using DFPT;


                                                  2
```
