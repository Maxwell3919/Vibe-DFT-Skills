# plumed_quick_ref.pdf — page 15

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `a63efa7d4bb6cdd6ebe7e119a900b54dede258ecd6a8a23dad19876573e443f7`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   200.000         1.433853674         0.200000000          0.005555556     10.000
   400.000         1.431075271         0.200000000          0.004147748     10.000
   600.000         1.431419655         0.200000000          0.003334619     10.000
   800.000         1.509148410         0.200000000          0.002937840     10.000
  1000.000         1.683639369         0.200000000          0.003660780     10.000
  1200.000         1.680674151         0.200000000          0.002997952     10.000

   Then you can sum up the Gaussians and plot it with gnuplot.

sum_hills.x -ndim 1 -ndw 1 -file HILLS -out fes.dat

    The sum hills code could also be used to check the convergence of a metadynamics
simulation. This can be easily achieved by calculating the estimate of the FES at
regular interval in time using the -stride option and then evaluating the free energy
at different time steps. Just run sum hills:

sum_hills.x -out fes.dat -ndim 1 -ndw 1 -stride 150

    and you will get fes.dat, the FES for the whole simulation and fes.dat.1,
fes.dat.2 ..., one every stride Gaussians. You can plot free energy estimate at
different time steps as shown in Fig. 5.




                            Figure 5: Free energy surface


    From the Fig. 5, we can see that the lowest saddle point is at 1.43 Bohr, which
is the bond length of the hydrogen molecule and it takes 0.113 Hartree = 3.09 eV to
break this bond.

                                         15
```
