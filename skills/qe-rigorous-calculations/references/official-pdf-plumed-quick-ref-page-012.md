# plumed_quick_ref.pdf — page 12

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `86cfe028ea0c1a1041925d080626c5e70cb165329429b665ae0400578c5c065f`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
                       Figure 3: The time population of CVs


   200.000         3.578429291         5.750272190          0.300000000           0.300000000
                   0.001000000      0.000
   240.000         3.606928115         5.732241302          0.300000000           0.300000000
                   0.001000000      0.000

   where:

   • the first column contains the time t (in internal unit of the MD code which is
     a.u. here in BOMD) at which the Gaussian was deposited;

   • the following 2 columns contain the centroid of the Gaussian, Si (R(t)), one for
     each CV i;

   • the following 2 columns contain the Gaussian sigma σi , one for each CV i;

   • the last but one column contains the value of W ;

   • the last column is meaningful only in well-tempered metadynamics simulations
     (see the next example).

    This file will be used to calculate the estimate of the free energy at the end of our
metadynamics calculation.
    In order to restart a metadynamics run, the flag RESTART must be added to plumed.dat
after flag HILLS. This allows a metadynamics simulation to be restarted after an in-
terruption or after a run has finished. The HILLS files will be read at the beginning of
the simulation and the bias potential applied to the dynamics. Note that the presence

                                         12
```
