# plumed_quick_ref.pdf — page 14

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `f2e721f98bce4f571db6a77df524c559ab552f5e5561a1a1c5e5dd0f1ade8a73`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
pw.x). In WT metadynamics, the Gaussian height W is automatically rescaled during
the simulations following:

                                               V (S, t)
                                 W = W0 exp −                                     (6)
                                                kB ∆T
    where W0 is the initial Gaussian height and ∆T a parameter with the dimension
of a temperature. The use of Eq. 6 guarantees that the bias potential converges in a
single simulation and does not oscillate around the FES value, causing the problem of
overfilling as what we got in Fig. 4.
                                               ∆T
                         V (S, t → ∞) = −            F (S) + C                   (7)
                                            T + ∆T
    where T is the temperature of the system and C a constant.
    The quantity T + ∆T is often referred as the (fictitious) CV temperature, while
the ratio (T + ∆T )/T as bias factor. For the details of WT metadynamics, please see
references[8, 2]. To perform a WT metadynamics simulation with PLUMED you have
to use the directive WELLTEMPERED and specify one of the parameters described above
using either the keyword CV TEMPERTURE or BIASFACTOR. In addition, the temperature
of the system must be specified explicitly with SIMTEMP.
    Here are some practical rules to choose wisely the parameters in WT metadynamics
simulations:

   • The bias factor (or equivalently the CV temperature) regulates how fast the
     amount of bias potential added decreases with simulation time and eventually
     controls the extent of exploration. The choice of these parameters depends on
     the typical free-energy barriers involved in the process under study. Note that
     this parameter can be changed on-the-fly as needed.
   • The optimal choice of the initial Gaussian height W0 is less crucial and at the
     same time less trivial. It is irrelevant in the long time regime and affects only
     the transient part of the simulation. A short initial filling period can be desirable
     if the transverse degrees of freedom relax quickly, otherwise a moderate initial
     energy rate is a better choice.

   The following is an example of input file for this WT metadynamics simulation at
300 K with a bias factor 10 and an initial Gaussian height of 0.005.

PRINT    W_STRIDE 5
HILLS    HEIGHT 0.005 W_STRIDE 10
WELLTEMPERED SIMTEMP 300 BIASFACTOR 10
DISTANCE LIST 1 2 SIGMA 0.2
ENDMETA

    In WT metadynamics, the Gaussians height as written in the HILLS file is multiplied
by the factor (T + ∆T )/∆T . This guarantees that when you sum the Gaussians (by
means for example of the sum hills code) you get directly the FES. The last column
of the HILLS file contains the value of the bias factor used in the WT metadynamics
simulation. For this example, the HILLS file looks like:

                                           14
```
