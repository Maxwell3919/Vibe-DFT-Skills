# brillouin_zones.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/brillouin_zones.pdf
- Retrieved: 2026-07-17T11:53:22+00:00
- Official source SHA-256: `debca2c4482e2488b38a4cef3ff92bff200bf2aa4f316d0ad45abe859d5fc0aa`
- Extracted text SHA-256: `3b33ca965c7107f80756d88c3b756e9ee1dee0aa993f97359481eed73567aada`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
1     Brillouin zone
Quantum ESPRESSO (QE) support for the definition of high symmetry lines inside the Bril-
louin zone (BZ) is still rather limited. However QE can calculate the coordinates of the vertexes
of the BZ and of particular points inside the BZ. These notes show the shape and orientation
of the BZ used by QE. The principal direct and reciprocal lattice vectors, as implemented in
the routine latgen, are illustrated here together with the labels of each point. These labels
can be given as input in a band or phonon calculation to define paths in the BZ. This feature
is available with the option tpiba b or crystal b in a ’bands’ calculation or with the option
q in band form in the input of the matdyn.x code. BEWARE: you need to explicitly specify
ibrav to use this feature. Lines in reciprocal space are defined by giving the coordinates of
the starting and ending points and the number of points of each line. The coordinates of the
starting and ending points can be given explicitly with three real numbers or by giving the
label of a point known to QE. For example:
X 10
gG 25
0.5 0.5 0.5 1
indicate a path composed by two lines. The first line starts at point X, ends at point Γ, and
has 10 k points. The second line starts at Γ, ends at the point of coordinates (0.5,0.5,0.5)
and has 25 k points. Greek labels are prefixed by the letter g: gG indicates the Γ point, gS
the Σ point etc. Subscripts are written after the label: the point P1 is indicated as P1. In
the following section you can find the labels of the points defined in each BZ. There are many
conventions to label high symmetry points inside the BZ. The variable point label type
selects the set of labels used by QE. The default is point label type=’SC’ and the labels
have been taken from W. Setyawan and S. Curtarolo, Comp. Mat. Sci. 49, 299 (2010).
Other choices can be more convenient in other situations. The names reported in the web
pages http://www.cryst.ehu.es/cryst/get kvec.html are available for some BZ. You can
use them by setting (point label type=’BI’), others can be added in the future. This option
is available only with ibrav̸=0 and for all positive ibrav with the exception of the base centered
monoclinic (ibrav=13), and triclinic (ibrav=14) lattices. In these cases you have to give all
the coordinates of the k-points.

1.1    ibrav=1, simple cubic lattice
The primitive vectors of the direct lattice are:
                                        a1 = a(1, 0, 0),
                                        a2 = a(0, 1, 0),
                                        a3 = a(0, 0, 1),
while the reciprocal lattice vectors are:
                                              2π
                                       b1 =      (1, 0, 0),
                                               a
                                              2π
                                       b2   =    (0, 1, 0),
                                               a
                                              2π
                                       b3   =    (0, 0, 1).
                                               a
                                                   2
```
