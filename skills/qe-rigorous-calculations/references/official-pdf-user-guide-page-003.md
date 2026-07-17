# user_guide.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `8fe64e59ddf47ca29f8fc03b8ad6ab15426aadacf81f6dc475b5edf3fd289afc`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   • QEHeat: energy current in insulators for thermal transport calculations.

   • KCW: quasiparticle energies of finite and extended systems using Koopmans-compliant
     functionals in a Wannier representation.

The following auxiliary packages are included as well:

   • PWgui: a Graphical User Interface, producing input data files for PWscf and some PostProc
     codes.

   • atomic: atomic calculations and pseudopotential generation.

Several additional packages that exploit data produced by Quantum ESPRESSO or patch
some Quantum ESPRESSO routines can be downloaded and build together with Quantum
ESPRESSO, notably: make:

   • Wannier90: maximally localized Wannier functions.

   • WanT: quantum transport properties with Wannier functions.

   • YAMBO: electronic excitations within Many-Body Perturbation Theory, GW and Bethe-
     Salpeter equation.

   • D3Q: anharmonic force constants.

   • GIPAW (Gauge-Independent Projector Augmented Waves): NMR chemical shifts and EPR
     g-tensor.

For Quantum ESPRESSO with the self-consistent continuum solvation (SCCS) model, aka
“Environ”, see http://www.quantum-environment.org/.
    Documentation on single packages can be found in the Doc/ directory of each package.
A detailed description of input data is available for most packages in files INPUT *.txt and
INPUT *.html.
    The Quantum ESPRESSO codes work on many different types of Unix machines, in-
cluding parallel machines using both OpenMP and MPI (Message Passing Interface), as well
as machines running Mac OS X or MS-Windows. Since Feb.2021 NVidia GPU’s are supported
by the stable releases. AMD GPU’s are also supported but not yet in the main repository and
in stable releases.
    Further documentation, beyond what is provided in this guide, can be found in:

   • the Doc/ and examples/ directories of the Quantum ESPRESSO distribution;

   • the web site www.quantum-espresso.org;

   • the archives of the mailing list: see section 1.2, “Contacts”, for more info;

   • the Wiki pages on GitLab: https://gitlab.com/QEF/q-e/-/wikis. People who want
     to contribute to Quantum ESPRESSO should read these!




                                               3
```
