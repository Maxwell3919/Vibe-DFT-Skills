# plumed_quick_ref.pdf — page 13

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `408b7ce07cd35cf26572f5ba9adbee940e0cd979ba20bd0bfdbfc932368433d9`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
of the RESTART flag only affects the metadynamics part of the simulation, and thus the
usual procedure for restarting a MD run must be followed.

3.3.1    Free energy reconstruction
In the long-time limit, the bias potential of metadynamics converges to the free energy
changed in sign[7]. At any time during the simulation we can sum the Gaussians
deposited so far and obtain the current estimate of the free energy surface (FES) using
the utility sum hills as we compiled in the previous section.

sum_hills.x -file HILLS -out fes.dat -ndim 2 -ngrid 100 100

   The file in output fes.dat contains the estimate of the free energy calculated on
a regular grid whose dimension is specified by -ngird. These parameters should be
chosen with care. To calculate accurately the potential in a given point of the CV
space, a practical rule is to choose the bin size to be half the Gaussian sigma.
   As usual, you can plot the 3D FES with gnuplot:

set pm3d
sp "fes.dat" w pm3d

    and you will get a plot like that in Fig. 4




                     Figure 4: Free energy surface of SN2 reaction




4       Second worked example: H-H
In this example, well-tempered (WT) metadynamics[8] will be employed to reconstruct
the FES of the hydrogen molecule within Born-Oppenheimer approximation (with



                                           13
```
