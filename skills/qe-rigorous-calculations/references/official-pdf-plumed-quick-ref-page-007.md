# plumed_quick_ref.pdf — page 7

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `f8f4056927ed2062220939462fe18f2d8fa6ae15f657d314c0d12f7c926eca49`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
                          Figure 1: A sketch of SN2 reaction


(pw.x) and then Car-Parrinello molecular dynamics (CP-MD) (cp.x). The electronic
structure is computed within density functional theory (DFT) using the PBE exchange-
correlation functional. Ultra-soft pseudo-potentials are used for the valence electrons,
and the wave function is expanded in a plane waves basis set up to an kinetic energy
cutoff of 25 Ry and charge density cutoff of 200 Ry. An orthorhombic P supercell of
18 * 12 * 12 a.u.3 is used. The temperature of the system is 300 K via ”soft” velocity
rescaling in BO-MD and Nose-Hoover thermostat in CP-MD.

3.3    Metadynamics with Born-Oppenheimer molecular dynam-
       ics
For Metadynamics a possible input plumed.dat can be

# switching on metadynamics and Gaussian parameters
HILLS HEIGHT 0.001 W_STRIDE 2
# instruction for CVs printout
PRINT W_STRIDE 1
# the distance between C-Cl’ and C-Cl
DISTANCE LIST 1 3 SIGMA 0.3
DISTANCE LIST 2 3 SIGMA 0.3
# WALLS: prevent to depart the two mols
UWALL CV 1 LIMIT 7.0 KAPPA 100.0
LWALL CV 1 LIMIT 2.5 KAPPA 100.0
UWALL CV 2 LIMIT 7.0 KAPPA 100.0
LWALL CV 2 LIMIT 2.5 KAPPA 100.0
# end of the input
ENDMETA


                                           7
```
