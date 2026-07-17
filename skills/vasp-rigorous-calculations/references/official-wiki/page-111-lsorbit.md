# LSORBIT

- Official URL: https://www.vasp.at/wiki/LSORBIT
- Page ID: 111
- Revision ID: 27887
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

LSORBIT = .TRUE. | .FALSE.
Default: LSORBIT = .FALSE.

Description: Switch on spin-orbit coupling.

LSORBIT = True switches on spin-orbit coupling (SOC)[1] and automatically sets LNONCOLLINEAR = True. It requires using vasp_ncl. SOC couples the spin degrees of freedom with the lattice degrees of freedom. We recommend carefully checking the symmetry and convergence of your results when using SOC; see below.

LSORBIT only works for PAW potentials and is not supported by ultrasoft pseudopotentials. It is supported as of VASP.4.5.

Contents

- 1 Assumptions and output

- 2 Symmetry and convergence

- 3 Related tags and articles

- 4 References

Assumptions and output[edit | edit source]

- Switching on spin-orbit coupling (SOC) adds an additional term [math]\displaystyle{ H^{\alpha\beta}_{soc}\propto\mathbf{\sigma}\cdot\mathbf{L} }[/math] to the Hamiltonian that couples the Pauli-spin operator [math]\displaystyle{ \mathbf{\sigma} }[/math] with the angular momentum operator [math]\displaystyle{ \mathbf{L} }[/math].[1] As a relativistic correction, SOC acts predominantly in the immediate vicinity of the nuclei. Therefore, it is assumed that contributions of [math]\displaystyle{ H_{soc} }[/math] outside the PAW spheres are negligible. Hence, VASP calculates the matrix elements of [math]\displaystyle{ H_{soc} }[/math] only for the all-electron one-center contributions

[math]\displaystyle{
E_{soc}^{ij} = \delta_{{\bf R}_i{\bf R}_j}\delta_{l_il_j} \sum_{n \bf k} w_{\bf k} f_{n\bf k} \sum_{\alpha\beta} \langle \tilde{\psi}^\alpha_{n\bf k} |\tilde{p}_i \rangle \langle \phi_i | H^{\alpha\beta}_{soc} | \phi_j \rangle \langle \tilde{p}_j | \tilde{\psi}^\beta_{n\bf k} \rangle
}[/math]
where [math]\displaystyle{ \phi_i({\bf r}) = R_i(|{\bf r}-{\bf R}_i|) Y_{l_im_i}(\theta,\varphi) }[/math] are the partial waves of an atom centered at [math]\displaystyle{ {\bf R}_i }[/math], [math]\displaystyle{ \tilde{\psi}^\alpha_{n\bf k} }[/math] is the spinor-component [math]\displaystyle{ \alpha=\uparrow,\downarrow }[/math] of the pseudo-orbital with band-index n and Bloch vector k, and [math]\displaystyle{ f_{n\bf k} }[/math] and [math]\displaystyle{ w_{\bf k} }[/math] are the Fermi- and k-point weights, respectively.[1]

- It is possible to write the partial magnetization by setting LORBIT, i.e., the site- and orbital-resolved expectation value of the Pauli-spin operator [math]\displaystyle{ \mathbf{\sigma} }[/math]. And the partial orbital angular momentum by setting LORBMOM, i.e., the site- and orbital-resolved expectation value of the orbital angular momentum operator [math]\displaystyle{ \mathbf{L} }[/math].

Mind: The orbital angular momentum (vector-like quantity) is written to the OUTCAR file in Cartesian coordinates, while the magnetic moments (spinor-like quantity) are read and written in the basis specified by SAXIS (spinor space).

The default orientation of spinor space is [math]\displaystyle{ \sigma_1=\hat x }[/math], [math]\displaystyle{ \sigma_2 =\hat y }[/math], [math]\displaystyle{ \sigma_3 = \hat z }[/math]. Hence, the bases agree by default, and no transformation is required.

- After a successful calculation including SOC, VASP writes the following results to the OUTCAR file:

Spin-Orbit-Coupling matrix elements

Ion: 1 E_soc: -0.0984080
l= 1
0.0000000 -0.0134381 -0.0134381
-0.0134381 0.0000000 -0.0134381
-0.0134381 -0.0134381 0.0000000
l= 2
0.0000000 -0.0005072 0.0000000 -0.0005072 -0.0024560
-0.0005072 0.0000000 -0.0018420 -0.0005072 -0.0006140
0.0000000 -0.0018420 0.0000000 -0.0018420 0.0000000
-0.0005072 -0.0005072 -0.0018420 0.0000000 -0.0006140
-0.0024560 -0.0006140 0.0000000 -0.0006140 0.0000000
l= 3
0.0000000 -0.0000000 0.0000000 0.0000000 0.0000000 -0.0000000 -0.0000000
-0.0000000 0.0000000 -0.0000000 0.0000000 -0.0000000 -0.0000000 -0.0000000
0.0000000 -0.0000000 0.0000000 -0.0000000 -0.0000000 -0.0000000 0.0000000
0.0000000 0.0000000 -0.0000000 0.0000000 -0.0000000 0.0000000 0.0000000
0.0000000 -0.0000000 -0.0000000 -0.0000000 0.0000000 -0.0000000 0.0000000
-0.0000000 -0.0000000 -0.0000000 0.0000000 -0.0000000 0.0000000 -0.0000000
-0.0000000 -0.0000000 0.0000000 0.0000000 0.0000000 -0.0000000 0.0000000

Here, 1 E_soc represents the accumulated energy contribution [math]\displaystyle{ E_{soc}=\sum_{ij} E_{soc}^{ij} }[/math] inside the augmentation sphere that is centered at [math]\displaystyle{ {\bf R}_1 }[/math] (position of ion 1), while the following entries correspond to the matrix elements [math]\displaystyle{ E_{soc}^{ij} }[/math] for the angular momentum [math]\displaystyle{ l }[/math]. Rows and columns correspond to [math]\displaystyle{ m }[/math] and [math]\displaystyle{ m' }[/math] of the real spherical harmonics [math]\displaystyle{ Y_{lm} }[/math](see Angular functions for naming and ordering conventions).

Symmetry and convergence[edit | edit source]

In any spin-polarized (ISPIN=2) or noncollinear (LNONCOLLINEAR=T) calculation, even without SOC, the total energy depends on the relative orientation of magnetic moments. For instance, two magnetic sites may couple ferromagnetically or antiferromagnetically. On the other hand, the total energy is independent of the orientation of the magnetic moments with respect to the lattice without SOC. For instance, in-plane and out-of-plane moments on a surface would yield the same energy in the absence of SOC.

Switching on SOC couples the spin degrees of freedom that live in spinor space and the lattice degrees of freedom that live in real space, see SAXIS. Therefore, the in-plane and out-of-plane magnetic moments on a surface would yield different energies, when including SOC. Similarly, the ferromagnetically or antiferromagnetically ordered magnetic moments may additionally align with, e.g., the third lattice vector by setting LSORBIT = True.

Generally, be extremely diligent when using SOC: The energy differences can be of the order of few [math]\displaystyle{ \mu }[/math]eV/atom, k-point convergence is tedious and slow, and the required compute time might be huge, even for small cells.

Warning: When SOC is included, we recommend testing whether switching off symmetry (ISYM=-1) changes the results.

Often, the k-point set changes from one to the other spin orientation, thus worsening the transferability of the results. Note that the WAVECAR file cannot be reread properly if the number of k-points changes. Hence, restart the calculation without symmetry from a converged charge density by setting ICHARG=1! Also, consider the setting of LMAXMIX.

We recommend setting GGA_COMPAT = False for noncollinear calculations since this improves the numerical precision of GGA calculations.

Please check the sections on LNONCOLLINEAR, SAXIS, LMAXMIX, and GGA_COMPAT.

Related tags and articles[edit | edit source]

LNONCOLLINEAR,
MAGMOM,
SAXIS,
LORBMOM,
LORBIT,
LMAXMIX,
GGA_COMPAT

Examples that use this tag

References[edit | edit source]

- ↑ a b c S. Steiner, S. Khmelevskyi, M. Marsman, and G. Kresse, Phys. Rev. B 93, 224425 (2016).
