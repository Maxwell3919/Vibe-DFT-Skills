# pseudo-gen.pdf — page 21

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `6ae429f1905975fd51759dc7bbe44c7680c625435014654fbfa2d255c67e3520`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
      n l      nl                e AE (Ry)             e PS (Ry)     De AE-PS (Ry)
      1 0      3S    1( 2.00)         -4.60347            -4.60348         0.00001
      2 1      3P    1( 6.00)         -2.85621            -2.85623         0.00002
      3 2      3D    1( 2.00)         -0.31302            -0.31301        -0.00001
      2 0      4S    1( 2.00)         -0.32830            -0.32892         0.00062
      3 1      4P    1( 0.00)         -0.10777            -0.10732        -0.00045

Note that the 3s, 3p, 3d levels should be the same by construction (the difference is
numerical noise); the 4s and 4p levels are not guaranteed to be the same. The fact
that they are, to a very good degree, is very reassuring. A look at the orbitals will
reveal that 3s, 3p, 3d are nodeless, 4s and 4p have one node. The spherical wave basis
set confirms the absence of ghosts:

    Cutoff (Ry) :       50.0
                               N = 1         N = 2          N = 3
      E(L=0) =           -4.5385 Ry     -0.3263 Ry      -0.0047 Ry
      E(L=1) =           -2.8427 Ry     -0.1071 Ry       0.0193 Ry
      E(L=2) =           -0.1511 Ry      0.0311 Ry       0.0685 Ry

      Cutoff (Ry) :     100.0
                               N = 1         N = 2          N = 3
      E(L=0) =           -4.5883 Ry     -0.3279 Ry      -0.0048 Ry
      E(L=1) =           -2.8547 Ry     -0.1073 Ry       0.0193 Ry
      E(L=2) =           -0.2918 Ry      0.0303 Ry       0.0649 Ry

      Cutoff (Ry) :     150.0
                               N = 1         N = 2          N = 3
      E(L=0) =           -4.5899 Ry     -0.3280 Ry      -0.0048 Ry
      E(L=1) =           -2.8549 Ry     -0.1073 Ry       0.0193 Ry
      E(L=2) =           -0.2936 Ry      0.0303 Ry       0.0649 Ry

Note that for l = 0 the first (N = 1) level is the 3s level, the second (N = 2) level
is the 4s level, and the like for l = 1. Let us now repeat the testing on the nine
selected configurations as for the 4-electron PP. You will have to add 3s2 3p6 to all
test configurations configts. Let us see check the errors on total energy differences:

$ grep Delta ld1.test
     dEtot_ps =       0.227291 Ry,          Delta E=         -0.001230 Ry
     dEtot_ps =       0.540886 Ry,          Delta E=         -0.000918 Ry
     dEtot_ps =       1.540155 Ry,          Delta E=         -0.002640 Ry
     dEtot_ps =       0.343314 Ry,          Delta E=          0.000077 Ry
     dEtot_ps =       0.715061 Ry,          Delta E=          0.001142 Ry
     dEtot_ps =       1.849816 Ry,          Delta E=         -0.000820 Ry
     dEtot_ps =       3.522904 Ry,          Delta E=         -0.004735 Ry
     dEtot_ps =       6.702626 Ry,          Delta E=         -0.003032 Ry

Energy differences are reproduced with an error that does not exceed a few mRy (see
column at the rhs). Eigenvalues are also well reproduced, e.g.:
```
