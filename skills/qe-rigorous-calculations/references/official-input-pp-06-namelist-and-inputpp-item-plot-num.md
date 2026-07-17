# INPUT_PP — NAMELIST: &INPUTPP — Item: plot_num

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `566a80dca9483ecb0b5fcf586dc1a1a1c178195c6b63c8d76765374ab7dbc0c5`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


plot_num

INTEGER

Default:

-1

Selects what to save in filplot:

-1 = do not do anything, skip step (1) (see header)

0 = electron (pseudo-)charge density

1 = total potential V_bare + V_H + V_xc

2 = local ionic potential V_bare

3 = local density of states at specific energy or grid of energies
(number of states per volume, in bohr^3, per energy unit, in Ry)

4 = local density of electronic entropy

5 = STM images
Tersoff and Hamann, 
PRB 31, 805 (1985)

6 = spin polarization (rho(up)-rho(down))

7 = contribution of selected wavefunction(s) to the
(pseudo-)charge density. For norm-conserving PPs,
|psi|^2 (psi=selected wavefunction). Noncollinear case:
contribution of the given state to the charge or
to the magnetization along the direction indicated
by spin_component (0 = charge, 1 = x, 2 = y, 3 = z )

8 = electron localization function (ELF)

9 = charge density minus superposition of atomic densities

10 = integrated local density of states (ILDOS)
from 
emin
to 
emax
(emin, emax in eV)
if 
emax
is not specified, 
emax
=E_fermi

11 = the V_bare + V_H potential

12 = the sawtooth electric field potential (if present)

13 = the noncollinear magnetization.

17 = all-electron valence charge density
can be performed for PAW calculations only
requires a very dense real-space grid!

18 = The exchange and correlation magnetic field in the noncollinear case

19 = Reduced density gradient
( J. Chem. Theory Comput. 7, 625 (2011), 
doi:10.1021/ct100641a
)
Set the isosurface between 0.3 and 0.6 to plot the
non-covalent interactions (see also plot_num = 20)

20 = Product of the electron density (charge) and the second
eigenvalue of the electron-density Hessian matrix;
used to colorize the RDG plot (plot_num = 19)

21 = all-electron charge density (valence+core).
For PAW calculations only; requires a very dense real-space grid.

22 = kinetic energy density

23 = the charge density of states between emin & emax

123 = DORI: density overlap regions indicator
(
doi: 10.1021/ct500490b
) Implemented by D. Yang & Q.Liu

24 = Reconstructed all-electron charge

25 = Squared modulus of the Hubbard projector function of DFT+U

[
Back to Top
]

IF 
plot_num = 0 or 9
:

Options for total charge (plot_num=0)
or for total minus atomic charge (plot_num=9):
```
