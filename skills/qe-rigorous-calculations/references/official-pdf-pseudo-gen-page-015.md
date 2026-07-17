# pseudo-gen.pdf — page 15

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `77afad931f3f1d3ae3574e42546a5c5549ccf3de5e39e7bd3bf1d650a52428b8`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’,
   iswitch=2
 /
 &test
   file_pseudo=’Ti.pbe-n-rrkj.UPF’,
   nconf=1, configts(1)=’3d2 4s2 4p0’,
   ecutmin=50, ecutmax=200, decut=50
 /
This will solve the Kohn-Sham equation for the PP read from file pseudo, for a single
valence configuration (nconf=1) listed in configts(1) (the ground state in this case),
using a base of spherical waves whose cutoff (in Ry) ranges from ecutmin to ecutmax
in steps of decut. The initial part of the output looks good, but let us look at the test
with spherical waves, towards the end:
       Cutoff (Ry) :         200.0
                                   N = 1             N = 2              N = 3
       E(L=0) =               -0.7483 Ry         -0.3282 Ry          -0.0042 Ry
       E(L=1) =               -0.1077 Ry          0.0192 Ry           0.0630 Ry
       E(L=2) =               -0.2961 Ry          0.0304 Ry           0.0654 Ry
The lowest levels found in this way should be the same1 as those calculated from radial
integration (see above). This is true for the 4p state (-0.1077 Ry), for the 3d state
(-0.2961 Ry vs -0.31302 Ry, see footnote), for the 4s state (-0.3282 Ry)....but note the
spurious 4s level at -0.7483 Ry! Our PP has a ghost and is unusable.
    What should be do now? we may try to change the definition of the local potential.
We had chosen l = 1, let us try l = 2 and l = 0. The former has the same pathology,
the latter has no ghosts. So our data for PP generation are as follows:
 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’,
   rlderiv=2.90, eminld=-2.0, emaxld=2.0, deld=0.01, nld=3,
   iswitch=3
 /
 &inputp
   pseudotype=1, nlcc=.true., lloc=0,
   file_pseudopw=’Ti.pbe-n-rrkj.UPF’,
 /
3
4P 2 1 0.00 0.00 2.9 2.9
3D 3 2 2.00 0.00 1.3 1.3
4S 1 0 2.00 0.00 2.9 2.9
(note lloc=0 and the 4s state at the end of the list). Let us plot again logarithmic
derivatives and orbitals (they look quite the same as before) and run again the test
with spherical waves. We get (see the last section in the output):
   1
    actually there are numerical differences, especially large for localized states like 3d, whose origin
is under investigation
```
