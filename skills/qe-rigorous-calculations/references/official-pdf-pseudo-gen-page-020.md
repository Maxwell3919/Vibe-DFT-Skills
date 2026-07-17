# pseudo-gen.pdf — page 20

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `519611f56754d06048afc9b505667821ef3441d9443e9e8961e34b81a42a2d36`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3.2    Single-projector, norm-conserving, with semicore states
The results of transferability tests suggest that a Ti PP with only 3d, 4s, 4p states have
limited transferability to cases with different 3d configurations. In order to improve it,
a possible way is to put semicore 3s and 3p states in valence. The maximum for those
states (0.87 a.u. and 0.90 a.u. respectively) is in the same range as for 3d (0.98 a.u.).
Let us try thus the following:

 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’,
   rlderiv=2.90, eminld=-4.0, emaxld=2.0, deld=0.01, nld=3,
   iswitch=3
 /
 &inputp
   pseudotype=1, rho0=0.001, ...
   file_pseudopw=’Ti.pbe-sp-rrkj.UPF’
 /
3
3S 1 0 2.00 0.00 1.1 1.1
3P 2 1 6.00 0.00 1.2 1.2
3D 3 2 2.00 0.00 1.3 1.3
 &test
   configts(1)=’3s2 3p6 3d2 4s2 4p0’,
 /

Note the presence of the &test namelist: it is used in this context to supply the
electronic valence configuration, to be used for unscreening. As a first step, we do not
include the core correction. In place of the dots we should specify the local reference
potential. If we use lloc=-1 with large values of rcloc, (comparable to pseudization
radii for the previous case) we get all kinds of mysterious errors:

      from compute_chi : error #                  1
      n is too large

for rcloc=2.5, while rcloc=2.7 produces an equally mysterious

      from run_pseudo : error #                  1
      Errors in PS-KS equation

while smaller values (e.g. 1.5) lead to other errors:

      WARNING! Expected number of nodes: 0 = 2-1-1, number of nodes found: 1.

Even if the code doesn’t stop, the presence of such messages is a signal of something
going wrong in the generation algorithm. With some more experiments, though, one
finds that rcloc=1.3 yields a good potential. We still have other choices. In this case,
d as reference potential: lloc=2, seems to work as well (and produces a PP with less
projectors: only s and p). The generation algorithm in the latter case yields these
results for Kohn-Sham energies:
```
