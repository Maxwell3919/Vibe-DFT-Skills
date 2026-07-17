# pseudo-gen.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `b7a967414423da886ede93bbc7d65806162f34ec2a08a0c5032e67870a471d00`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
     You are advised to perform also the test with a basis set of spherical Bessel functions
jl (qr). In addition to revealing the presence of “ghosts”, this test also gives an idea
of the smoothness of the potential: the dependence of energy levels upon the cutoff in
the kinetic energy is basically the same for the pseudo-atom in the basis of jl (qr)’s and
for the same pseudo-atom in a solid-state calculation using PW’s.
     Another way to check for transferability is to compare AE and pseudo (PS) loga-
rithmic derivatives, also calculated by ld1.x. Typically this comparison is done on the
reference configuration, but not necessarily so. You should supply on input:
    – the radius rd at which logarithmic derivatives are calculated (rd should be of the
      order of the ionic or covalent radius, and larger than any of the rc ’s)
    – the energy range Emin , Emax and the number of points for the plot. The energy
      range should cover the typical valence one-electron energy range expected in the
      targeted application of the PP.
The files containing logarithmic derivatives can be easily read and plotted using for
instance the plotting program gnuplot or xmgrace. Sizable discrepancies between AE
and PS logarithmic derivatives are a sign of trouble (unless your energy range is too
large or not centered around the range of pseudization energies, of course).
    Note that the above checks, based on atomic calculations only, do not replace the
usual checks (convergence tests, bond lengths, etc) one has to perform in at least some
simple solid-state or molecular systems before starting a serious calculation.


3     A worked example: Ti
Let us consider the Ti atom: Z = 22, electronic configuration: 1s2 2s2 2p6 3s2 3p6 3d2 4s2 ,
with PBE XC functional. The input data for the AE calculation is simple:
 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’
 /
and yields the total energy and Kohn-Sham levels. Let us concentrate on the outermost
states:
      3 0       3S 1( 2.00)              -4.6035            -2.3017           -62.6334
      3 1       3P 1( 6.00)              -2.8562            -1.4281           -38.8608
      3 2       3D 1( 2.00)              -0.3130            -0.1565            -4.2588
      4 0       4S 1( 2.00)              -0.3283            -0.1641            -4.4667
      4 1       4P 1( 0.00)              -0.1078            -0.0539            -1.4663
and on their spatial extension:
s(3S/3S) =     1.000000     <r> =     1.0069    <r2> =       1.1699     r(max) =      0.8702
s(3P/3P) =     1.000000     <r> =     1.0860    <r2> =       1.3907     r(max) =      0.8985
s(3D/3D) =     1.000000     <r> =     1.6171    <r2> =       3.5729     r(max) =      0.9811
s(4S/4S) =     1.000000     <r> =     3.5138    <r2> =      14.2491     r(max) =      2.9123
s(4P/4P) =     1.000000     <r> =     4.8653    <r2> =      27.9369     r(max) =      3.8227
```
