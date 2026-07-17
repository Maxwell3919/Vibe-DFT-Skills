# plumed_quick_ref.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `b3b33f21bb9889a0c0e582b37e4e7d306542540b0a3824c9db9e2013745abe7c`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
[-ndw 1 ...      ] (CVs for the free energy surface)
[-ngrid 50 ...   ] (mesh dimension. DEFAULT :: 100)
[-dp ...         ] (size of the mesh of the output free energy)
[-fix 1.1 ...    ] (define the region for the FES, if omitted this is
                   automatically calculated)
[-stride 10      ] (how often the FES is written)
[-cutoff_e 1.e-6 ] (the hills are cutoff at 1.e-6)
[-cutoff_s 6.25 ] (the hills are cutoff at 6.25 standard deviations from
                   the center)
[-2pi x          ] ([0;2pi] periodicity on the x CV, if -fix is not used 2pi
                   is assumed)
[-pi x           ] ([-pi;pi] periodicity on the x CV, if -fix is not used 2pi
                   is assumed)
[-kt 0.6         ] (kT in the energy units)
[-grad           ] (apply periodicity using degrees)
[-bias <biasfact>] (writing output the bias for a well tempered metadynamics run)
[-file HILLLS    ] (input file)
[-out fes.dat    ] (output file)
[-hills nhills   ] (number of gaussians that are read)


3     First worked example: SN2 reaction
3.1    SN2 reaction in vacuum
In this section, we will show a very simple chemical reaction done with Quantum
ESPRESSO code with PLUMED plugin. The goal of this example is to study the free
energy for the reaction depicted in Fig. 1. This SN2 reaction between Cl− and CH3Cl
shows the symmetric transition state and the CH3 conversion of configuration known
as the Walden inversion[6].

3.2    Choice of CVs and simulation details
The first thing you should decide is the collective variables (CVs) to be used:

    • Distance?

    • Does the angle matter?

    • Torsion?

    • Coordination number?

    • Anything else?

   Here we choose the bond length of C-Cl as CV1 and the bond length of C-Cl− as
CV2. The simulation will be performed using the Born-Oppenheimer molecular dy-
namics (BO-MD) algorithm as implemented in the Quantum ESPRESSO program


                                           6
```
