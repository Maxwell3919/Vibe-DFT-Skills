# SAXIS

- Official URL: https://www.vasp.at/wiki/SAXIS
- Page ID: 187
- Revision ID: 36604
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

SAXIS = [real array]
Default: SAXIS = (0, 0, 1)

Description: Set the global spin-quantization axis w.r.t. Cartesian coordinates.

SAXIS specifies the relative orientation of spinor space spanned by the Pauli matrices [math]\displaystyle{ \{\sigma_1 }[/math], [math]\displaystyle{ \sigma_2 }[/math], [math]\displaystyle{ \mathbf{\sigma}_3\} }[/math] with respect to Cartesian coordinates [math]\displaystyle{ \{\hat x, \hat y, \hat z\} }[/math]. The default is [math]\displaystyle{ \sigma_1=\hat x }[/math], [math]\displaystyle{ \sigma_2 =\hat y }[/math], [math]\displaystyle{ \sigma_3 = \hat z }[/math].
The direction of the spin-quantization axis [math]\displaystyle{ \sigma_3 }[/math] with respect to Cartesian coordinates is set

SAXIS = sx sy sz ! global spin-quantization axis

such that [math]\displaystyle{ \sigma_3=\mathbf{s}/|\mathbf{s}| }[/math], i.e., [math]\displaystyle{ \sigma_3 }[/math] points along [math]\displaystyle{ \mathbf{s}=(s_x,s_y,s_z)^T }[/math]. The directions of [math]\displaystyle{ \sigma_1 }[/math] and [math]\displaystyle{ \sigma_2 }[/math] are a consequence of rotating [math]\displaystyle{ \sigma_3 }[/math] to point along [math]\displaystyle{ \mathbf{s} }[/math] as described below.

The relative orientation of spinor space with respect to real space becomes important in case spin-orbit coupling is included (LSORBIT=True). All magnetic moments and spinor-like quantities written or read by VASP are given in the basis of the spinor space [math]\displaystyle{ \{\sigma_1 }[/math], [math]\displaystyle{ \sigma_2 }[/math], [math]\displaystyle{ \mathbf{\sigma}_3\} }[/math]. This includes the MAGMOM tag in the INCAR file, the total and local magnetizations in the OUTCAR and PROCAR file, the spinor-like orbitals in the WAVECAR file, and the magnetization density in the CHGCAR file.

Warning: SAXIS ≠ 0 0 1, is not supported for Hartree-Fock calculations and hybrid functionals (LHFCALC = .TRUE.)! These methods set ISYM = 3, which only works with the default SAXIS. You can still use SAXIS with ISYM = -1., but in most cases it is computationally more efficient to change MAGMOM instead.

Coordinate system[edit | edit source]

Fig 1. Euler angles [math]\displaystyle{ \alpha }[/math] and [math]\displaystyle{ \beta }[/math] defined by [math]\displaystyle{ \mathbf{s}=(s_x,s_y,s_z)^T }[/math].

The default orientation is [math]\displaystyle{ \sigma_1=\hat x }[/math], [math]\displaystyle{ \sigma_2 =\hat y }[/math], [math]\displaystyle{ \sigma_3 = \hat z }[/math].
To set [math]\displaystyle{ \hat{\sigma}_3=s/|s| }[/math], VASP applies two rotations with Euler angles

[math]\displaystyle{
\begin{align}
\alpha&=\arctan2\left(\frac{s_y}{s_x}\right) \in [-\pi,\pi]\\
\beta&=\arctan2\left(\frac{\sqrt{s_x^2+s_y^2}}{s_z}\right) \in [0,\pi].
\end{align}
}[/math]

Here, [math]\displaystyle{ \alpha }[/math] is the angle between the projection of SAXIS onto the xy plane (sx,sy,0) and the Cartesian vector [math]\displaystyle{ \hat x }[/math], and [math]\displaystyle{ \beta }[/math] is the angle between the vector SAXIS and the Cartesian vector [math]\displaystyle{ \hat z }[/math], see Fig. 1. Search for `Euler angles` in the OUTCAR file to see what VASP uses. For the default [math]\displaystyle{ \mathbf{s}=(0,0,1) }[/math], [math]\displaystyle{ \alpha=0 }[/math] and [math]\displaystyle{ \beta=0 }[/math].

The transformation of a vector [math]\displaystyle{ \mathbf{m}=(m_1,m_2,m_3)^T }[/math] given in the basis [math]\displaystyle{ \{\sigma_1 }[/math], [math]\displaystyle{ \sigma_2 }[/math], [math]\displaystyle{ \mathbf{\sigma}_3\} }[/math] into [math]\displaystyle{ \mathbf{m}'=(m_x,m_y,m_z)^T }[/math] in Cartesian coordinates and its inverse transformation read

[math]\displaystyle{
\begin{align}
\mathbf{m}&= m_1 \sigma_1 + m_2 \sigma_2 + m_3 \sigma_3 \\
\mathbf{m}'&= m_x \hat x + m_y \hat y + m_z \hat z \\
\mathbf{m}'&= R_z^\alpha R_y^\beta \mathbf{m} \\
\mathbf{m} &= R_y^{-\beta} R_z^{-\alpha} \mathbf{m}' \\
\end{align}
}[/math]

where the rotation matrices are

[math]\displaystyle{
R_z^\alpha = \left(\begin{matrix}
\cos(\alpha) & -\sin(\alpha) & 0 \\
\sin(\alpha) & \cos(\alpha) & 0 \\
0 & 0 & 1 \\
\end{matrix}\right), \quad
R_y^\beta = \left(\begin{matrix}
\cos(\beta) & 0 & \sin(\beta) \\
0 & 1 & 0 \\
-\sin(\beta) & 0 & \cos(\beta) \\
\end{matrix}\right).
}[/math]

Mind: Apply the proper basis transformation when comparing vector-like quantities and spinor-like quantities.

For instance, when LORBMOM=True the orbital angular momentum is written to the OUTCAR file in Cartesian coordinates. Thus, when comparing the orbital angular momentum (vector-like quantity) and the magnetization (spinor-like quantity), one has to perform a basis transformation on one of the quantities unless the bases agree (default).

Example[edit | edit source]

- In case the bases have the same orientation, i.e., [math]\displaystyle{ \sigma_1=\hat x }[/math], [math]\displaystyle{ \sigma_2 =\hat y }[/math], [math]\displaystyle{ \sigma_3 = \hat z }[/math] (default)

[math]\displaystyle{
\begin{align}
m_x & = & m_1, \\
m_y & = & m_2, \\
m_z & = & m_3.
\end{align}
}[/math]
For a single site this implies setting

MAGMOM = mx my mz ! magnetic moment in Cartesian coordinates
SAXIS = 0 0 1 ! default

Fig 2. Example with [math]\displaystyle{ \mathbf{s}=(1,1,0)^T }[/math] and Euler angles [math]\displaystyle{ \alpha=\pi/4 }[/math] and [math]\displaystyle{ \beta=\pi/2 }[/math].

- Another good choice is setting [math]\displaystyle{ \mathbf{s} }[/math] to point along the direction of the on-site magnetic moment such that

[math]\displaystyle{
\begin{align}
m_x & = & \sin(\beta)\cos(\alpha) m &= m\, s_x / \sqrt{s_x^2+s_y^2+s_z^2} \\
m_y & = & \sin(\beta)\sin(\alpha) m &= m\, s_y / \sqrt{s_x^2+s_y^2+s_z^2} \\
m_z & = & \cos(\beta) m &= m\, s_z / \sqrt{s_x^2+s_y^2+s_z^2},
\end{align}
}[/math]
where [math]\displaystyle{ m }[/math] is the total on-site magnetic moment.
For a single site, this case implies setting

MAGMOM = 0 0 m ! magnetic moment along sigma3
SAXIS = sx sy sz ! direction of sigma3

Thus, there are two methods to rotate the initial magnetization in an arbitrary direction: either by changing the initial magnetic moments MAGMOM or by changing SAXIS. Both methods should, in principle, yield exactly the same energy, but for implementation reasons, the second method might be more precise.

- In case

SAXIS = 1 1 0 ! alpha=pi/4, beta=pi/2

the spinor space [math]\displaystyle{ \{\sigma_1 }[/math], [math]\displaystyle{ \sigma_2 }[/math], [math]\displaystyle{ \mathbf{\sigma}_3\} }[/math] will be rotated with respect to real space [math]\displaystyle{ \{\hat x, \hat y, \hat z\} }[/math] as shown in Fig. 2.

Related tags and articles[edit | edit source]

LNONCOLLINEAR,
MAGMOM,
LSORBIT

Examples that use this tag
