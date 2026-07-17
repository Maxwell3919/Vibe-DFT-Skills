# pseudo-gen.pdf — page 16

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `fbd9011412ca868f7b01428a5a52526dc29fb815d1182345147d9e0130a0d094`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
        Cutoff (Ry) :      50.0
                                 N = 1          N = 2           N = 3
        E(L=0) =           -0.3282 Ry      -0.0049 Ry        0.0361 Ry
        E(L=1) =           -0.1077 Ry       0.0192 Ry        0.0630 Ry
        E(L=2) =           -0.1469 Ry       0.0311 Ry        0.0682 Ry

        Cutoff (Ry) :    100.0
                                N = 1           N = 2           N = 3
        E(L=0) =          -0.3282 Ry       -0.0049 Ry        0.0361 Ry
        E(L=1) =          -0.1077 Ry        0.0192 Ry        0.0630 Ry
        E(L=2) =          -0.2959 Ry        0.0303 Ry        0.0652 Ry
        Cutoff (Ry) :    150.0
                                N = 1           N = 2           N = 3
        E(L=0) =          -0.3282 Ry       -0.0049 Ry        0.0361 Ry
        E(L=1) =          -0.1077 Ry        0.0192 Ry        0.0630 Ry
        E(L=2) =          -0.2961 Ry        0.0303 Ry        0.0652 Ry

This time the first column yields (with a small discrepancy for 3d) the expected levels,
and only those levels. It is wise to inspect the second column as well for absence
of suspiciously low levels: ghosts may appear also as spurious excited states close to
occupied states. Note how bad the energy for the 3d level is at 50 Ry. At 100 Ry
however we are close to convergence and at 150 Ry well converged, in agreement with
the estimate given during the PP generation (138 Ry).
     We have now our first candidate (i.e. not surely wrong) PP. In order to 1) verify
if it really does the job, 2) quantify its transferability, 3) quantify its hardness, and 4)
improve it, if possible, we need to perform some more testing.

3.1.2    Testing
As a first idea of how good our PP is, let us verify how it behaves on differente electronic
configuration. The code allows to test several configurations in the following way:

 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’,
   iswitch=2
 /
 &test
   file_pseudo=’Ti.pbe-n-rrkj.UPF’,
   nconf=9
   configts(1)=’3d2 4s2 4p0’
   configts(2)=’3d2 4s1 4p1’
   configts(3)=’3d2 4s1 4p0’
   configts(4)=’3d2 4s0 4p0’
   configts(5)=’3d1 4s2 4p1’
   configts(6)=’3d1 4s2 4p0’
   configts(7)=’3d1 4s1 4p0’
   configts(8)=’3d1 4s0 4p0’
```
