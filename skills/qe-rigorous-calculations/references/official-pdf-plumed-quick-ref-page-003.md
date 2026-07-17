# plumed_quick_ref.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `133ab673dc8547c27a8d8c69a75d309786526ea7dbb12e5852b47dc402680f0e`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
every τG MD steps. The external (’metadynamics’) potential acting on the system at
time t is given by
                                                X                      (S(x) − s(t0 ))2
                 VG (S(x), t) = ω                              exp(−                    )       (3)
                                                                            2δs2
                                        t0   = τG , 2τG ,...
                                                t0 <t

    where s(t) = S(x(t)) is the value of CV at time t. Three parameters enter the
definition of the VG are the Gaussian height ω, the Gaussian width δs and the frequency
τG at which the Gaussians are added.
    If the Gaussians are large, the free energy surface will be explored at a fast pace,
but the reconstructed profile will be affected by large errors. Instead, if the Gaussians
are small or are placed infrequently the reconstruction will be accurate, but it will take
a longer time.
    A hint of the two different manners in which metadynamics can be used:

   • It can be used to ’escape free energy minima, i.e. to find the lowest free energy
     saddle point out of a local minimum. In this case the metadynamics should be
     stopped as soon as the walker exits from the minimum and starts exploring a
     new region of space.

   • It can be used to exhaustively explore a predefined region in the CV space and
     reconstruct the free energy surface. In this case the simulation should be stopped
     when the motion of the walker becomes diffusive in this region.

   The basic assumption of metadynamics is that VG (s, t) after a sufficiently long
time provides an estimate of the underlying free energy limt→∞ VG (s, t) − F (s). This
equation states that an equilibrium quantity, namely the free energy, can be estimated
by a non-equilibrium dynamics in which the underlying potential is changed every time
a new Gaussian is added.
   If the CV is a d-dimensional vector, namely two or more CVs are used at the same
time, the metadynamics potential is given by
                                                                  d
                                             X                    X (S(x) − s(t0 ))2
               VG (S(x), t) = ω                          exp(−                              )   (4)
                                                                              2δs2
                                  t0   = τG , 2τG ,...            α=1
                                          t0 <t

    and it is necessary to choose a width δsα for each CV. Metadynamics works properly
only if d is small, and that the quality of the reconstructed free energy is strongly
influenced by the parameters ω and δs. Large values for ω and δs allow for a fast
sampling of the CV space at the price of a low accuracy.
    For a detailed description, please see the references Laio et al.[2, 3].

1.2    Collective variables
The reliability of metadynamics is strongly influenced by the choice of the CVs. Ideally
the CVs should satisfy three properties:



                                                    3
```
