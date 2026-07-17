# IVDW

- Official URL: https://www.vasp.at/wiki/IVDW
- Page ID: 376
- Revision ID: 34375
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

IVDW = [integer]

Default: IVDW

= 0

(no correction)

Description: IVDW specifies a vdW dispersion term of the atom-pairwise or many-body type.

Available vdW atom-pairwise and many-body methods[edit | edit source]

With all methods listed below, a dispersion correction is added to the total energy, but also to the atomic forces and stress tensor, such that lattice relaxations, molecular dynamics, and vibrational analysis (via finite differences) can be performed. Note, however, that these correction schemes are currently not available for phonon calculations based on density functional perturbation theory.

IVDW=
Type
Description

1 or 10
pairwise
DFT-D2 method of Grimme.[1] Available as of VASP.5.2.11.

11
pairwise
DFT-D3 method of Grimme with zero-damping function.[2] Available as of VASP.5.3.4.

12
pairwise
DFT-D3 method with Becke-Johnson damping function.[3] Available as of VASP.5.3.4.

15
pairwise
DFT-D3 methods available in the simple-DFT-D3 library.[4][5][6] Available as of VASP.6.6.0 as external package.

13
pairwise
DFT-D4 method.[7][8][9] Available as of VASP.6.2 as external package.

3
pairwise
DFT-ulg[10] method. Available as of VASP.5.3.5.

4
pairwise
dDsC dispersion correction[11][12] method. Available as of VASP.5.4.1.

2 or 20
pairwise
Tkatchenko-Scheffler method.[13] Available as of VASP.5.3.3.

21
pairwise
Tkatchenko-Scheffler method with iterative Hirshfeld partitioning.[14][15] Available as of VASP.5.3.5.

202
many-body
Many-body dispersion energy method (MBD@rsSCS).[16][17] Available as of VASP.5.4.1.

263
many-body
Many-body dispersion energy with fractionally ionic model for polarizability method (MBD@rSC/FI).[18][19] Available as of VASP.6.1.0.

14
pairwise and many-body
One of the methods available in the library libMBD of many-body dispersion methods.[20][21][22] Available as of VASP.6.4.3 as external package.

Mind:

- The libMBD implementations (IVDW=14) of the Tkatchenko-Scheffler methods and their MBD extensions are much faster (analytical calculation of the forces) than the VASP implementations (numerical calculation of the forces). Therefore, it is strongly recommended to use the libMBD implementation if available.

- The parameter LVDW used in previous versions of VASP (5.2.11 and later) to activate the DFT-D2 method is now obsolete. If LVDW=.TRUE. is defined, IVDW is automatically set to 1 (unless IVDW is specified in INCAR).

Related tags and articles[edit | edit source]

DFT-D2,
DFT-D3,
simple-DFT-D3,
DFT-D4,
Tkatchenko-Scheffler method,
Self-consistent screening in Tkatchenko-Scheffler method,
Tkatchenko-Scheffler method with iterative Hirshfeld partitioning,
Many-body dispersion energy,
Many-body dispersion energy with fractionally ionic model for polarizability,
DFT-ulg,
dDsC dispersion correction,
LIBMBD_METHOD

See also the alternative vdW-DF functionals: LUSE_VDW, Nonlocal vdW-DF functionals.

Examples that use this tag

References[edit | edit source]

- ↑ S. Grimme, J. Comput. Chem. 27, 1787 (2006).

- ↑ S. Grimme, J. Antony, S. Ehrlich, and S. Krieg, J. Chem. Phys. 132, 154104 (2010).

- ↑ S. Grimme, S. Ehrlich, and L. Goerigk, J. Comput. Chem. 32, 1456 (2011).

- ↑ S. Ehlert, Simple dft-d3: library first implementation of the d3 dispersion correction, J. Open Source Softw. 9, 7169 (2024).

- ↑ https://dftd3.readthedocs.io

- ↑ https://github.com/dftd3

- ↑ E. Caldeweyher, S. Ehlert, A. Hansen, H. Neugebauer, S. Spicher, C. Bannwarth, and S. Grimme, J. Chem. Phys. 150, 154122 (2019).

- ↑ https://dftd4.readthedocs.io

- ↑ https://github.com/dftd4

- ↑ H. Kim, J.-M. Choi, and W. A. Goddard, III, J. Phys. Chem. Lett. 3, 360 (2012).

- ↑ S. N. Steinmann and C. Corminboeuf, J. Chem. Phys. 134, 044117 (2011).

- ↑ S. N. Steinmann and C. Corminboeuf, J. Chem. Theory Comput. 7, 3567 (2011).

- ↑ A. Tkatchenko and M. Scheffler, Phys. Rev. Lett. 102, 073005 (2009).

- ↑ T. Bučko, S. Lebègue, J. Hafner, and J. G. Ángyán, J. Chem. Theory Comput. 9, 4293 (2013)

- ↑ T. Bučko, S. Lebègue, J. G. Ángyán, and J. Hafner, J. Chem. Phys. 141, 034114 (2014).

- ↑ A. Tkatchenko, R. A. DiStasio, Jr., R. Car, and M. Scheffler, Phys. Rev. Lett. 108, 236402 (2012).

- ↑ A. Ambrosetti, A. M. Reilly, and R. A. DiStasio Jr., J. Chem. Phys. 140, 018A508 (2014).

- ↑ T. Gould and T. Bučko, C6 Coefficients and Dipole Polarizabilities for All Atoms and Many Ions in Rows 1–6 of the Periodic Table, J. Chem. Theory Comput. 12, 3603 (2016).

- ↑ T. Gould, S. Lebègue, J. G. Ángyán, and T. Bučko, A Fractionally Ionic Approach to Polarizability and van der Waals Many-Body Dispersion Calculations, J. Chem. Theory Comput. 12, 5920 (2016).

- ↑ https://libmbd.github.io/

- ↑ https://github.com/libmbd/

- ↑ J. Hermann, M. Stöhr, S. Góger, S. Chaudhuri, B. Aradi, R. J. Maurer, and A. Tkatchenko, libMBD: A general-purpose package for scalable quantum many-body dispersion calculations, J. Chem. Phys. 159, 174802 (2023).
