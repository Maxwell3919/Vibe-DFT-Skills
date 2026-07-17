# pseudo-gen.pdf — page 17

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `8366a8881f8a9f3d387397a491e5585f434cb1749c9a0093d18dcd32772e695e`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
        configts(9)=’3d0 4s0 4p0’
/

here we have chosen 9 different valence configurations (the corresponding AE config-
urations are obtained by superimposing configts to core states in config). Some
of them are neutral, some are ionic, the first five leave the 3d states unchanged, the
last one is a completely ionized Ti4+ . For each configuration, the code writes results
(e.g. orbitals) into files ld1N.∗ and ld1psN.∗, where N is the index of the configura-
tion. A summary is written to file ld1.test. For the first configuration, AE and PS
eigenvalues and total energies are written:

         3 2     3D   1( 2.00)              -0.31302       -0.31302        0.00000
         1 0     4S   1( 2.00)              -0.32830       -0.32830        0.00000
         2 1     4P   1( 0.00)              -0.10777       -0.10777        0.00000
         Etot =   -1707.131006 Ry,           -853.565503 Ha, -23226.698556 eV
         Etotps =    -9.748745 Ry,             -4.874372 Ha,    -132.638416 eV

(AE and PS eigenvalues are in this case the same, since this is the reference configura-
tion used to build the PP). For the following configurations, AE and PS eigenvalues,
plus total energy differences2 wrt configuration 1 are printed:

         3 2     3D     1( 2.00)        -0.40319                 -0.40457             0.00138
         1 0     4S     1( 1.00)        -0.38394                 -0.38420             0.00026
         2 1     4P     1( 1.00)        -0.15248                 -0.15237            -0.00011
         dEtot_ae =         0.226061 Ry
         dEtot_ps =         0.226250 Ry,    Delta E=                 -0.000189 Ry

The discrepancy between AE and PS energy differences (in this case, wrt the ground
state) as well as the discrepancies in AE and PS eigenvalues, are a measure of how
transferrable a PP is. In this case, the AE-PS discrepancy on δE = E(4s1 4p1 3d2 ) −
E(4s2 4p0 3d2 ) (look at Delta E) is quite small, < 0.2 mRy, while the maximum dis-
crepancy of the eigenvalues (rightmost column) ∼ 1 mRy. These are very good results.
Unfortunately this is also a configuration that doesn’t differ much from the reference
one. Let us see the other cases:

         3 2     3D     1( 2.00)        -0.83550                 -0.83256            -0.00295
         1 0     4S     1( 1.00)        -0.76075                 -0.76163             0.00088
         2 1     4P     1( 0.00)        -0.48549                 -0.48617             0.00068
         dEtot_ae =         0.539968 Ry
         dEtot_ps =         0.540344 Ry,    Delta E=                 -0.000376 Ry

         3 2     3D     1( 2.00)        -1.44648                 -1.44538            -0.00110
         1 0     4S     1( 0.00)        -1.24186                 -1.24652             0.00465
         2 1     4P     1( 0.00)        -0.91224                 -0.91599             0.00375
         dEtot_ae =         1.537516 Ry
         dEtot_ps =         1.540285 Ry,    Delta E=                 -0.002769 Ry
    2
    Reminder: absolute PS total energies depend upon the specific PP! Only energy differences are
significant.
```
