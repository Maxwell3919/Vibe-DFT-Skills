# LORBIT

- Official URL: https://www.vasp.at/wiki/LORBIT
- Page ID: 188
- Revision ID: 37170
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LORBIT = 0 | 1 | 2 | 5 | 10 | 11 | 12
Default: LORBIT = 0

Description: Selects a projection method onto local quantum numbers ([math]\displaystyle{ lm }[/math]) and writes PROCAR/PROOUT file.

When LORBIT is set, VASP performs a post-processing step of the Kohn-Sham (KS) orbitals to decompose the KS orbitals into local quantum numbers ([math]\displaystyle{ lm }[/math]) and obtain local properties, e.g., the on-site charge density or on-site magnetic moments due to the spin degrees of freedom. The decomposition is achieved by means of one of several projection methods selected by LORBIT. All these projections rely on the fact that most of the charge density is close to the ion center, and interstitial regions separate them well. This is merely a qualitative approach in contrast to performing a wannierization in order to obtain a localized basis, but often it serves as a good estimate.

Tip: As this is a post-processing step, LORBIT can be added/changed when restarting a converged calculation. To this end, set ALGO=None and the desired LORBIT, and restart from WAVECAR.

For VASP version < 6 with LORBIT >= 11 and ISYM = 2, see known issues.

Contents

- 1 Projection methods

- 1.1 For LORBIT < 10

- 1.2 For LORBIT >= 10

- 1.3 Phase factors

- 2 On-site partial charge densities and magnetization

- 3 Partial density of states (pDOS)

- 4 References

- 5 Related tags and articles

Projection methods[edit | edit source]

See the table for an overview:

LORBIT
RWIGS tag
files written

0
required
DOSCAR and PROCAR

1
required
DOSCAR and lm-decomposed PROCAR

2
required
DOSCAR and lm-decomposed PROCAR + phase factors

5
required
DOSCAR and PROOUT

10
ignored
DOSCAR and PROCAR

11
ignored
DOSCAR and lm-decomposed PROCAR

12
ignored
DOSCAR and lm-decomposed PROCAR + phase factors (not recommended)

13
ignored
DOSCAR and lm-decomposed PROCAR + phase factors, choose best projector for each band (not recommended)

14
ignored
DOSCAR and lm-decomposed PROCAR + phase factors, choose single projector for interval EMIN,EMAX

For LORBIT < 10[edit | edit source]

The projection is onto spherical harmonics at each ionic site within a sphere defined by RWIGS. The radius must be specified for each atomic species, and there is some uncertainty introduced depending on the size of the sphere.

For LORBIT >= 10[edit | edit source]

The projection uses the projector functions that are provided by the PAW method. This is, of course, still a qualitative approach because also, for the PAW projectors, the radius was somehow defined, and it is not guaranteed to be the best choice for that particular system as it depends on the chemical composition and crystal or molecular structure.

Phase factors[edit | edit source]

For LORBIT>=12:
The phase factors written by VASP can usually only be used as a qualitative measure of the projection of the orbitals into the atomic sphere. The main issue is that most VASP POTCAR files have two or three projectors per [math]\displaystyle{ l }[/math]-quantum number, and projecting an orbital onto two projectors will yield two complex numbers. VASP combines these two numbers into a single number. The precise algorithms differ in different versions of VASP, and we recommend that you inspect the source code for more details. From vasp.6 onward, an improved scheme has been implemented and can be selected using LORBIT=14. In this case, VASP first selects a single projector for each [math]\displaystyle{ l }[/math]-quantum number by linearly combining all projectors with the same [math]\displaystyle{ l }[/math]-quantum number. This is done in such a way that the new projector is optimally chosen to represent the calculated orbitals in the energy interval specified by EMAX and EMIN. In the second step, VASP projects onto these optimized projectors, yielding a single complex number for each orbital, site and [math]\displaystyle{ l }[/math]-quantum number, which is written to the PROCAR file. For details we also refer to [1].
LORBIT=12 should no longer be used except for qualitative calculations. LORBIT=13 chooses the projectors also automatically, but allows for different optimal linear combinations for each orbital.
Note that this is generally not desirable, since the resultant projection is not compatible with the required properties of a projection operator (a projection operator needs to use energy and orbital independent projectors).
Hence, do not use LORBIT=13 for anything but a qualitative analysis.

LORBIT=13 and LORBIT=14 are only supported by version >=5.4.4.

On-site partial charge densities and magnetization[edit | edit source]

The partial charge densities can be found in the OUTCAR

total charge

# of ion s p d tot
------------------------------------------
1 1.514 0.000 0.000 1.514
2 0.123 0.345 0.000 0.468

Here, the first column corresponds to the ion index [math]\displaystyle{ \alpha }[/math], the s, p, d,... columns correspond to the partial charges for [math]\displaystyle{ l=0,1,2,\cdots }[/math] defined as

[math]\displaystyle{ \rho_{\alpha l}=\frac{1}{N_{\bf k}} \sum_{n{\bf k}}f_{n{\bf k}} \sum_{m=-l}^{l}|\langle Y_{lm}^{\alpha}|\phi_{n\mathbf{k}}\rangle|^2
}[/math]

The [math]\displaystyle{ \langle Y_{lm}^{\alpha}|\phi_{n\mathbf{k}}\rangle }[/math] are obtained from the projection of the (occupied) KS orbitals [math]\displaystyle{ |\phi_{n{\bf k}}\rangle }[/math] onto spherical harmonics that are non zero within spheres of a radius RWIGS centered at ion [math]\displaystyle{ \alpha }[/math] and the last column is the sum [math]\displaystyle{ \sum_{l}\rho_{\alpha l} }[/math].

Note that depending on the system, an "f" column is written as well.

- In case of spin-polarized magnetic calculations (ISPIN=2), the partial magnetization densities are written to the OUTCAR

magnetization (x)

# of ion s p d tot
------------------------------------------
1 0.000 0.000 0.000 0.000
2 0.000 0.245 0.000 0.245

Here, the magnetization density is calculated from the difference in the up and down spin channel [math]\displaystyle{ m^{\alpha l}_z = \rho_{\alpha l}^{\uparrow}-\rho_{\alpha l}^{\downarrow}
}[/math]
Although the direction of the magnetization densities is meaningless in a spin-polarized calculation (no spin-orbit coupling, see LSORBIT), here the projection axis is the z-axis. This is consistent withe the behavior upon restarting a noncollinear calculation from a spin-polarized one with default SAXIS.

- In case of noncollinear calculations (LNONCOLLINEAR=.TRUE.), the lines after "total charge" correspond to the diagonal average

[math]\displaystyle{ \frac{\rho_{\alpha l}^{\uparrow\uparrow} - \rho_{\alpha l}^{\downarrow \downarrow}}{2} }[/math]
of the density tensor

[math]\displaystyle{
\rho_{\alpha l} = \left(\begin{matrix}
\rho_{\alpha l}^{\uparrow \uparrow } & \rho_{\alpha l}^{\uparrow \downarrow} \\
\rho_{\alpha l}^{\downarrow \uparrow} & \rho_{\alpha l}^{\downarrow \downarrow} \\
\end{matrix}\right),
}[/math]

which is determined from the projected components

[math]\displaystyle{
\rho^{\mu\nu}_{\alpha l} = \frac{1}{N_{\bf k}} \sum_{n{\bf k}}f_{n{\bf k}} \sum_{m=-l}^{l}
\langle \chi_{n {\bf k}}^\mu | Y_{lm}^\alpha \rangle
\langle Y_{lm}^\alpha | \chi_{n {\bf k}}^\nu \rangle
}[/math]

of the spinor [math]\displaystyle{ |\Psi_{n{\bf k}}\rangle=\left(\begin{matrix}\chi_{n{\bf k}}^\uparrow \\\chi_{n{\bf k}}^\downarrow \end{matrix}\right) }[/math]

Similarly, the lines after "magnetization (x)", "magnetization (y)", and "magnetization (z)"correspond to the partial magnetization density

[math]\displaystyle{
m_{\alpha l}^j = \frac{1}{2}\sum_{\mu,\nu=1}^2 \sigma^j_{\mu \nu} \rho_{\alpha l}^{\mu \nu}.
}[/math]

projected onto Pauli matrices [math]\displaystyle{ \{\sigma_1 }[/math], [math]\displaystyle{ \sigma_2 }[/math], [math]\displaystyle{ \mathbf{\sigma}_3\} }[/math]. By default, this corresponds to Cartesian directions [math]\displaystyle{ \sigma_1=\hat x }[/math], [math]\displaystyle{ \sigma_2 =\hat y }[/math], [math]\displaystyle{ \sigma_3 = \hat z }[/math], but the orientation can be changed using SAXIS.

Partial density of states (pDOS)[edit | edit source]

The partial density of states (pDOS) is the DOS projected onto specific ions or atomic orbitals. The output for it can be found in the following output files:

- PROCAR: the primary output for pDOS data. Each block lists the projection weight onto each atomic site and angular-momentum channel ([math]\displaystyle{ s }[/math], [math]\displaystyle{ p }[/math], [math]\displaystyle{ d }[/math], ...) for every band and k-point.

- vasprun.xml: the pDOS is stored in the <dos><partial> block, organized by ion and spin:

<dos>
<partial>
<array>
<dimension dim="1">gridpoints</dimension>
<dimension dim="2">spin</dimension>
<dimension dim="3">ion</dimension>
<field>energy</field>
<field>s</field>
<field>py</field>
<field>pz</field>
<field>px</field>
<field>dxy</field>
...
<set>
<set comment="ion 1">
<set comment="spin 1">
<r> -5.0000 5.5689 1.5445 1.5445 1.5445 0.0009 ... </r>
...

- vaspout.h5: pDOS data is accessible via py4vasp:

import py4vasp
calc = py4vasp.Calculation.from_path(".")

# Plot pDOS projected onto specific atoms (e.g., ions 3 and 5)
calc.dos.plot(selection="3, 5")

# Plot by element and orbital character
calc.dos.plot(selection="Fe(d)")

You can learn more about plotting and calculating it in our tutorials:

- Ni(100) surface

- NiO bulk

- CO molecule

- STM simulations

References[edit | edit source]

- ↑ M. Schüler, O.E. Peil, G.J. Kraberger, R. Pordzik, M. Marsman, G. Kresse, T.O. Wehling, and M. Aichhorn, J. Phys.: Condens. Matter 30, 475901 (2018).

Related tags and articles[edit | edit source]

RWIGS,
PROCAR,
PROOUT,
DOSCAR

Examples that use this tag
