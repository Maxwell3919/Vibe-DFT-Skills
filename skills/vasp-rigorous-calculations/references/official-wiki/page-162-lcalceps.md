# LCALCEPS

- Official URL: https://www.vasp.at/wiki/LCALCEPS
- Page ID: 162
- Revision ID: 33371
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LCALCEPS = .TRUE. | .FALSE.
Default: LCALCEPS = .FALSE.

Description: for LCALCEPS=.TRUE. the macroscopic ion-clamped static dielectric tensor, Born effective charge tensors, and the ion-clamped piezoelectric tensor of the system are determined from the response to finite electric fields.

For LCALCEPS=.TRUE., VASP calculates the ion-clamped static dielectric tensor

[math]\displaystyle{
\epsilon^\infty_{ij}=\delta_{ij}+
\frac{4\pi}{\epsilon_0}\frac{\partial P_i}{\partial \mathcal{E}_j},
\qquad
{i,j=x,y,z}
}[/math]

the Born effective charge tensors

[math]\displaystyle{
Z^*_{ij}=\frac{\Omega}{e}\frac{\partial P_i}{\partial u_j}
=\frac{1}{e}\frac{\partial F_j}{\partial \mathcal{E}_i},
\qquad
{i,j=x,y,z}
}[/math]

and the ion-clamped piezoelectric tensor of the system

[math]\displaystyle{
e^{(0)}_{ij}=-\frac{\partial \sigma_i}{\partial \mathcal{E}_j},
\qquad
{i=xx, yy, zz, xy, yz, zx}\quad{j=x,y,z}
}[/math]

from the self-consistent response to a finite electric field ε.
In this case, the "response" of the system is the change in the polarization P, the Hellmann-Feynman forces F, and the stress tensor σ. Mind the definition/sign convention of the stress tensor.

If this is combined with IBRION=6, the contribution from the ionic relaxations to the piezoelectric and dielectric tensors are calculated as well.

To this end VASP will perform essentially three successive calculations, with:

EFIELD_PEAD= εx 0 0

EFIELD_PEAD= 0 εy 0

EFIELD_PEAD= 0 0 εz

where, by default, VASP chooses εx=εy=εz=0.01 eV/Å.

This default may be overwritten by specifying

EFIELD_PEAD= εx εy εz

in the INCAR file.

The relevant output is found in the OUTCAR file, immediately following the lines (see the description of LEPSILON=.TRUE. as well):

MACROSCOPIC STATIC DIELECTRIC TENSOR (including local field effects)

BORN EFFECTIVE CHARGES (including local field effects)

PIEZOELECTRIC TENSOR (including local field effects)

In the above, "including local field effects" pertains to the fact that changes in the orbitals due to the electric field induce changes in the Hartree- and exchange-correlation potential. One may choose to limit this to changes in the Hartree potential alone, by specifying:

LRPA=.TRUE.

This is commonly referred to as the response within the "Random Phase Approximation" (RPA), or the "neglect of local field effects". The OUTCAR file will now contain additional sections, headed by the lines:

MACROSCOPIC STATIC DIELECTRIC TENSOR (excluding local field effects)

BORN EFFECTIVE CHARGES (excluding local field effects)

PIEZOELECTRIC TENSOR (excluding local field effects)

Important: For standard DFT functionals, ε∞, Z*, and e(0) may be more easily calculated from density functional perturbation theory (see LEPSILON = .TRUE.). For functionals that depend not only on the density but also explicitly on the orbitals, like hybrid functionals, density functional perturbation theory is presently not implemented and LEPSILON = .TRUE. is not applicable.

Warning: The piezoelectric tensor has the wrong sign in Vasp 5.4.4 and older. The bug is fixed with patch.5.4.4.16052018.gz.

Related tags and articles[edit | edit source]

LEPSILON,
LCALCPOL,
EFIELD_PEAD,
LPEAD,
IPEAD,
LBERRY,
IGPAR,
NPPSTR,
DIPOL,
IBRION,
Berry phases and finite electric fields

Examples that use this tag
