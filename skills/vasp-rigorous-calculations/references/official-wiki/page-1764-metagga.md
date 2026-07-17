# METAGGA

- Official URL: https://www.vasp.at/wiki/METAGGA
- Page ID: 1764
- Revision ID: 35874
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

METAGGA = [string]
Default: METAGGA = The functional specified by LEXCH in the POTCAR if GGA and XC are also not specified.

Description: Selects a meta-GGA exchange-correlation functional.

Mind:

- If you select a meta-GGA functional, make sure that you use POTCAR files that are suited for meta-GGA functionals. However, note that this requirement does not concern the deorbitalized meta-GGAs, i.e. those that do not depend on the kinetic-energy density, like SCAN-L.

- Depending on the meta-GGA that is chosen, it may be recommended to use a PAW potential that is more accurate than the standard/recommended one. This is particularly the case with functionals (e.g., MBJ or the Minnesota functionals like M06-L) that are very different from the standard ones like PBE or SCAN. The reason is that for such special functionals, using a PAW potential that includes more states in the valence or that is harder may be required to obtain results that are closer to the results that would be obtained with an all-electron code. That also means that it may be a good idea to do test calculations with different PAW potentials.

- For accuracy, it is strongly recommended to set LASPH=.TRUE. to account for aspherical contributions to the PAW one-centre terms.

- Since VASP.6.4.0 it is possible to use hybrid functionals that mix meta-GGA and Hartree-Fock exchange (AEXX). Furthermore, two new tags, AMGGAX and AMGGAC, were created.

- The XC tag, available since VASP.6.4.3, can be used to specify any linear combination of LDA, GGA and METAGGA exchange-correlation functionals.

- The results obtained with the meta-GGA functionals that depend on the Laplacian of the density [math]\displaystyle{ \nabla^2n }[/math] (e.g., SCAN-L) may not be reliable for large values of the energy cutoff ENCUT due to numerical instability. According to some tests, it is not recommended to use values of ENCUT above 800 eV.

Contents

- 1 Available functionals

- 2 POTCAR files: required information

- 3 Aspherical contributions related to one-center terms

- 4 Convergence issues

- 5 Related tags and articles

- 6 References

Available functionals[edit | edit source]

This table lists the meta-GGA functionals available in VASP. There are essentially two types of meta-GGAs, that differ in the variable on which they depend (in addition to [math]\displaystyle{ n }[/math] and [math]\displaystyle{ \nabla n }[/math]): the kinetic-energy density [math]\displaystyle{ \tau }[/math] or the Laplacian of the density [math]\displaystyle{ \nabla^2n }[/math]. The names of functionals which end with "_X" and "_C" correspond to exchange-only and correlation functionals, respectively. Note that the implementation of [math]\displaystyle{ \tau }[/math]-dependent meta-GGA functionals is described in [1].

METAGGA=
Variable
Description

LIBXC

Any MGGA from the external library Libxc.[2][3][4][5] It is necessary to have Libxc >= 5.2.0 installed and VASP.6.3.0 or higher compiled with precompiler options. The LIBXC1 and LIBXC2 tags (where examples are shown) are also required.

TPSS, TPSS_X or TPSS_C(1)
[math]\displaystyle{ \tau }[/math]

TPSS.[6]

RTPSS, RTPSS_X or RTPSS_C(1)
[math]\displaystyle{ \tau }[/math]

revTPSS is a revised version of TPSS.[7]

M06L, M06L_X or M06L_C(1)
[math]\displaystyle{ \tau }[/math]

M06-L.[8]

MS0, MS0_X or MS0_C(1)
[math]\displaystyle{ \tau }[/math]

MS0 corresponds to [math]\displaystyle{ \kappa=0.29 }[/math], [math]\displaystyle{ c=0.28771 }[/math] and [math]\displaystyle{ b=1.0 }[/math].[9][10]
Note that the correlation component, called vPBEc or regTPSS in the literature, is a GGA. Available since VASP.5.4.1.

MS1, MS1_X or MS1_C(1)
[math]\displaystyle{ \tau }[/math]

MS1 corresponds to [math]\displaystyle{ \kappa=0.404 }[/math], [math]\displaystyle{ c=0.18150 }[/math] and [math]\displaystyle{ b=1.0 }[/math].[10]
Note that the correlation component, called vPBEc or regTPSS in the literature, is a GGA. Available since VASP.5.4.1.

MS2, MS2_X or MS2_C(1)
[math]\displaystyle{ \tau }[/math]

MS2 corresponds to [math]\displaystyle{ \kappa=0.504 }[/math], [math]\displaystyle{ c=0.14601 }[/math] and [math]\displaystyle{ b=4.0 }[/math].[10]
Note that the correlation component, called vPBEc or regTPSS in the literature, is a GGA. Available since VASP.5.4.1.

SCAN, SCAN_X or SCAN_C(1)
[math]\displaystyle{ \tau }[/math]

SCAN.[11] May possibly lead to numerical instabilities. rSCAN or r[math]\displaystyle{ ^{2} }[/math]SCAN are more stable and should give similar results. Available since VASP.5.4.4.

RSCAN, RSCAN_X or RSCAN_C(1)
[math]\displaystyle{ \tau }[/math]

rSCAN is a regularized version of SCAN that is numerically more stable.[12]

R2SCAN, R2SCAN_X or R2SCAN_C(1)
[math]\displaystyle{ \tau }[/math]

r[math]\displaystyle{ ^{2} }[/math]SCAN is a regularized version of SCAN that is numerically more stable.[13] Available since VASP.6.2.0, or in version 5.4.4 by patch 4.

SREGTM1, SREGTM2 or SREGTM3
[math]\displaystyle{ \tau }[/math]

sregTM[14] versions 1, 2 or 3 of a regularized Tao-Mo functional.[15] Available since VASP.6.4.3.

TASK_X(2)
[math]\displaystyle{ \tau }[/math]
TASK exchange.[16] Available since VASP.6.5.0.

LAK, LAK_X or LAK_C
[math]\displaystyle{ \tau }[/math]
LAK.[17] Available since VASP.6.5.0.

MSPBEL, MSRPBEL or MSB86BL
[math]\displaystyle{ \tau }[/math]

MS-PBEl, MS-RPBEl or MS-B86bl.[18] Available since VASP.6.5.0.

RMSPBEL, RMSRPBEL or RMSB86BL
[math]\displaystyle{ \tau }[/math]

rMS-PBEl, rMS-RPBEl or rMS-B86bl.[19] Available since VASP.6.5.0.

SCANL
[math]\displaystyle{ \nabla^2n }[/math]

SCAN-L[20][21] is a deorbitalized version of SCAN. Available since VASP.6.4.0.

RSCANL
[math]\displaystyle{ \nabla^2n }[/math]

rSCAN-L is a deorbitalized version of rSCAN. Available since VASP.6.4.0.

R2SCANL
[math]\displaystyle{ \nabla^2n }[/math]

r[math]\displaystyle{ ^2 }[/math]SCAN-L is a deorbitalized versions of r[math]\displaystyle{ ^2 }[/math]SCAN.[22][23] Available since VASP.6.4.0.

OFR2
[math]\displaystyle{ \nabla^2n }[/math]

Orbital-free regularized-restored SCAN (OFR2).[23] Available since VASP.6.4.0.

SREGTM2L
[math]\displaystyle{ \nabla^2n }[/math]

v2-sregTM-L is a deorbitalized versions of v2-sregTM.[24] Available since VASP.6.4.0.

MBJ(3)
[math]\displaystyle{ \nabla^2n,\tau }[/math]

Modified Becke-Johnson potential.[25][26] The CMBJA, CMBJB and CMBJE tags correspond to [math]\displaystyle{ \alpha }[/math], [math]\displaystyle{ \beta }[/math] and the power [math]\displaystyle{ e=1/2 }[/math] (that can be modified) in Eq. (3) of Ref. [26], respectively. The default values are [math]\displaystyle{ \alpha=-0.012 }[/math], [math]\displaystyle{ \beta=1.023 }[/math] bohr[math]\displaystyle{ ^{1/2} }[/math] and [math]\displaystyle{ e=1/2 }[/math].[26]

LMBJ(3)
[math]\displaystyle{ \nabla^2n,\tau }[/math]

The local MBJ (LMBJ) potential.[27][28] The CMBJA, CMBJB, CMBJE, SMBJ, and RSMBJ tags correspond to [math]\displaystyle{ \alpha }[/math], [math]\displaystyle{ \beta }[/math], the power [math]\displaystyle{ e=1 }[/math] (that can be modified) of [math]\displaystyle{ \bar{g} }[/math], [math]\displaystyle{ \sigma }[/math] and [math]\displaystyle{ r_{s}^{\mathrm{th}} }[/math] in Eqs. (5)-(7) of Ref. [28], respectively. The default values are (see erratum of Ref. [28]) [math]\displaystyle{ \alpha=0.488 }[/math], [math]\displaystyle{ \beta=0.5 }[/math] bohr, [math]\displaystyle{ e=1 }[/math], [math]\displaystyle{ \sigma=2 }[/math] [math]\displaystyle{ \AA }[/math] ([math]\displaystyle{ =3.78 }[/math] bohr), and [math]\displaystyle{ r_{s}^{\mathrm{th}}=7 }[/math] bohr (which corresponds to [math]\displaystyle{ n_{\mathrm{th}}=6.96\times10^{-4} }[/math] e/bohr[math]\displaystyle{ ^{3} }[/math]).

(1) The exchange-only and correlation-only implementations are available since VASP.6.4.3.

(2) In Ref. [16] TASK exchange is combined with LDA-PW92 correlation.[29] This can be done with XC=TASK_X PW92_C in INCAR.

(3) A few points about the MBJ and LMBJ potentials:

- These are potential-only methods, i.e., there is no corresponding exchange-correlation energy [math]\displaystyle{ E_{xc} }[/math]. The used expression for [math]\displaystyle{ E_{xc} }[/math] is LDA, which is an arbitrary choice. This means that MBJ and LMBJ calculations can never be self-consistent with respect to the total energy, and thus we cannot compute Hellmann-Feynman forces (i.e., no ionic relaxation, etc.). Actually, these potentials aim solely at a description of the electronic properties, primarily the band gap, or magnetic moments.

- MBJ and LMBJ calculations may converge very slowly, so the number of maximum electronic steps (NELM) should be set higher than usual.

- In the presence of an extended vacuum region (e.g., surfaces) or an interface, the average of [math]\displaystyle{ |\nabla n|/n }[/math] has no meaning. Therefore, MBJ calculations should be done with a fixed value of [math]\displaystyle{ c }[/math], which can be done with the CMBJ tag., or alternatively with the LMBJ that was proposed for the purpose to be applicable to systems with vacuum or interfaces.

POTCAR files: required information[edit | edit source]

Calculations with a meta-GGA that depends on the kinetic-energy density require POTCAR files that include information on the kinetic-energy density of the core electrons. Almost all recent POTCAR files do fulfill this requirement, but there are some notable exceptions like O_GW. To check whether a particular POTCAR contains this information, type:

grep kinetic POTCAR

This should yield at least the following lines (for each element on the file):

kinetic energy-density
mkinetic energy-density pseudized

and for PAW datasets with partial core corrections:

kinetic energy density (partial)

Mind: For POTCAR files without core electrons (H, He, Li_sv, Be_sv, and _GW variants thereof) the grep command given above will not return the line about pseudized kinetic energy-density, since all electrons are considered as valence. These potentials can nevertheless be used for all meta-GGA functionals.

Aspherical contributions related to one-center terms[edit | edit source]

LASPH =.TRUE. should be selected if a meta-GGA functional is selected. If LASPH =.FALSE.,
the one-center contributions are only calculated for a spherically averaged density and kinetic-energy
density. This means that the one-center contributions to the Kohn-Sham potential are also spherical.
Since the PAW method describes the entire space using plane waves, errors are often small even
if the non-spherical contributions to the Kohn-Sham potential are neglected inside the PAW spheres
(additive augmentation, as opposed to the APW or FLAPW method where the plane wave contribution only
describes the interstitial region between the atoms). Anyhow, if the density is strongly non-spherical
around some atoms in your structure, LASPH =.TRUE. must be selected. Non-spherical terms are particularly encountered
in d- and f-elements, dimers, molecules, and solids with strong directional bonds.

Convergence issues[edit | edit source]

If convergence problems are encountered, it is recommended to preconverge the
calculations using the PBE functional and start the calculation from the WAVECAR file corresponding to the PBE ground state. Furthermore,
ALGO = A (conjugate gradient algorithm for orbitals) is often more stable
than charge density mixing, in particular if the system contains vacuum regions.

Related tags and articles[edit | edit source]

LIBXC1,
LIBXC2,
GGA,
XC,
CMBJ,
CMBJA,
CMBJB,
CMBJE,
SMBJ,
RSMBJ,
LASPH,
LMAXTAU,
LMIXTAU,
LASPH,
AMGGAX,
AMGGAC,
Band-structure calculation using meta-GGA functionals

Examples that use this tag

References[edit | edit source]

- ↑ J. Sun, M. Marsman, G. Csonka, A. Ruzsinszky, P. Hao, Y.-S. Kim, G. Kresse, and J. P. Perdew, Phys. Rev. B 84, 035117 (2011).

- ↑ M. A. L. Marques, M. J. T. Oliveira, and T. Burnus, Comput. Phys. Commun., 183, 2272 (2012).

- ↑ S. Lehtola, C. Steigemann, M. J. T. Oliveira, and M. A. L. Marques, SoftwareX, 7, 1 (2018).

- ↑ F. Tran, S. Lehtola, S. Pittalis, and M. A. L. Marques, Semi-Local Exchange-Correlation Approximations in Density Functional Theory, arXiv 2602.17333 (2026).

- ↑ https://libxc.gitlab.io

- ↑ J. Tao, J. P. Perdew, V. N. Staroverov, and G. E. Scuseria, Climbing the Density Functional Ladder: Nonempirical Meta–Generalized Gradient Approximation Designed for Molecules and Solids, Phys. Rev. Lett. 91, 146401 (2003).

- ↑ J. P. Perdew, A. Ruzsinszky, G. I. Csonka, L. A. Constantin, and J. Sun, Workhorse Semilocal Density Functional for Condensed Matter Physics and Quantum Chemistry, Phys. Rev. Lett. 103, 026403 (2009).

- ↑ Y. Zhao and D. G. Truhlar, J. Chem. Phys. 125, 194101 (2006).

- ↑ J. Sun, B. Xiao, and A. Ruzsinszky, J. Chem. Phys. 137, 051101 (2012).

- ↑ a b c J. Sun, R. Haunschild, B. Xiao, I. W. Bulik, G. E. Scuseria, and J. P. Perdew, J. Chem. Phys. 138, 044113 (2013).

- ↑ J. Sun, A. Ruzsinszky, and J. P. Perdew, Phys. Rev. Lett. 115, 036402 (2015).

- ↑ A. P. Bartók and J. R. Yates, J. Chem. Phys. 150, 161101 (2019).

- ↑ J. W. Furness, A. D. Kaplan, J. Ning, J. P. Perdew, and J. Sun, J. Phys. Chem. Lett. 11, 8208 (2020).

- ↑ H. Francisco, A. C. cancio, and S. B. Trickey, Reworking the Tao–Mo exchange-correlation functional. I. Reconsideration and simplification, J. Chem. Phys. 159, 214102 (2023).

- ↑ J. Tao and Y. Mo, Accurate Semilocal Density Functional for Condensed-Matter Physics and Quantum Chemistry, Phys. Rev. Lett. 117, 073001 (2015).

- ↑ a b T. Aschebrock and S. Kümmel, Ultranonlocality and accurate band gaps from a meta-generalized gradient approximation, Phys. Rev. Res. 1, 033082 (2019)

- ↑ T. Lebeda, T. Aschebrock, and S. Kümmel, Balancing the Contributions to the Gradient Expansion: Accurate Binding and Band Gaps with a Nonempirical Meta-GGA, Phys. Rev. Lett. 133, 136402 (2024).

- ↑ E. W. S. Smeets, J. Voos, and G.-J. Kroes, J. Phys. Chem. A 123, 5395 (2019).

- ↑ Y. Cai, R. Michiels, F. De Luca, E. Neyts, X. Tu, A. Bogaerts, and N. Gerrits, J. Phys. Chem. C 128, 8611 (2024).

- ↑ D. Mejía-Rodríguez and S. B. Trickey, Deorbitalization strategies for meta-generalized-gradient-approximation exchange-correlation functionals, Phys. Rev. A 91, 052512 (2017).

- ↑ D. Mejia-Rodriguez and S. B. Trickey, Deorbitalized meta-GGA exchange-correlation functionals in solids, Phys. Rev. B 98, 115161 (2018).

- ↑ D. Mejía-Rodríguez and S. B. Trickey, Meta-GGA performance in solids at almost GGA cost, Phys. Rev. B 102, 121109(R) (2020).

- ↑ a b A. D. Kaplan and J. P. Perdew, Phys. Rev. Mater. 6, 083803 (2022).

- ↑ H. Francisco, A. C. cancio, and S. B. Trickey, Reworking the Tao–Mo exchange–correlation functional. II. De-orbitalization, J. Chem. Phys. 159, 214103 (2023).

- ↑ A. D. Becke and E. R. Johnson, J. Chem. Phys. 124, 221101 (2006).

- ↑ a b c F. Tran and P. Blaha, Phys. Rev. Lett. 102, 226401 (2009).

- ↑ T. Rauch, M. A. L. Marques, and S. Botti, Local Modified Becke-Johnson Exchange-Correlation Potential for Interfaces, Surfaces, and Two-Dimensional Materials, J. Chem. Theory Comput. 16, 2654 (2020).

- ↑ a b c T. Rauch, M. A. L. Marques, and S. Botti, Accurate electronic band gaps of two-dimensional materials from the local modified Becke-Johnson potential, Phys. Rev. B 101, 245163 (2020).

- ↑ J. P. Perdew and Y. Wang, Phys. Rev. B 45, 13244 (1992).
