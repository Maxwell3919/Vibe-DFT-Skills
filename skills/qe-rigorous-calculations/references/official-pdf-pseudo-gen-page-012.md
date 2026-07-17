# pseudo-gen.pdf — page 12

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `97e9d0f1373b21bb78769a98e915cd1945ae8b37a40edb0125a459d0ac178c31`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Note that the 3d state has a small spatial extension, comparable to that of 3s and 3p
states and much smaller than for 4s and 4p states; the 3d energy is instead comparable
to that of 4s and 4p states and much higher than the 3s and 3p energies.. Much of
the chemistry of Ti is determined by its 3d states. What should we do? We have the
choice among several possibilities:

  1. single-projector NC-PP with 4 electrons in valence (3d2 4s2 ), with nonlinear core
     correction;

  2. single-projector NC-PP with 12 electrons in valence (3s2 3p6 3d2 4s2 );

  3. multiple-projector US-PP with 12 electrons in valence;

  4. multiple-projector US-PP with 4 electrons in valence and nonlinear core correc-
     tion;

  5. ...

The PP of case 1) will be hard due to the presence of 3d states, and its transferability
may turn out not be sufficient for all purposes; PP’s for 2) will be even harder due
to the presence of 3d and semicore 3s and 3p states; PP 3) can be made soft, but
generating one is not trivial; PP 4) may suffer from insufficient transferability.

3.1     Single-projector, norm-conserving, no semicore
3.1.1      Generation
Let us start from the simplest case with the following input:

 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’,
   rlderiv=2.90, eminld=-2.0, emaxld=2.0, deld=0.01, nld=3,
   iswitch=3
 /
 &inputp
   pseudotype=1, nlcc=.true., lloc=1,
   file_pseudopw=’Ti.pbe-n-rrkj.UPF’
 /
3
4S 1 0 2.00 0.00 2.9 2.9
3D 3 2 2.00 0.00 1.3 1.3
4P 2 1 0.00 0.00 2.9 2.9

In the &input namelist, we specify the we want to generate a PP (iswitch=3) and
to calculate nld=3 logarithmic derivatives at rlderiv=2.90 a.u. from the origin, in
the energy range eminld=-2.0 Ry to emaxld=2.0 Ry, in energy steps deld=0.01 Ry
(note that these values will not affect PP generation). In the &inputp namelist, we
specify the we want a single-projector, NC-PP (pseudotype=1), with nonlinear core
correction (nlcc=.true.), using the l = 1 channel as local (lloc=1). The output PP
```
