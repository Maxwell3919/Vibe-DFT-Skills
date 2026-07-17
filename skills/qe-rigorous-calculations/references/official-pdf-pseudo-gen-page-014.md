# pseudo-gen.pdf — page 14

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `abcc240f7aa32551bfc86218b99d9c28dfe4ea6709fa464ad0fd0917edbdad26`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
      1 0               4S            1( 2.00)                       -0.32830                    -0.32830          0.00000
      3 2               3D            1( 2.00)                       -0.31302                    -0.31302          0.00000
      2 1               4P            1( 0.00)                       -0.10777                    -0.10777          0.00000

You should get exactly 0 (within numerical accuracy) in the columnn at the right.
    As a further check, let’s have a look at the logaritmic derivatives and at pseudized
Kohn-Sham orbitals. Logarithmic derivatives are written to files ld1.dlog and ld1ps.dlog,
for AE and PS calculations respectively (file names can be changed using variable
prefix). They can be plotted using for instance gnuplot and the following commands:

plot [-2:2][-20:20] ’ld1.dlog’ u 1:2 w l lt 1, ’ld1.dlog’ u 1:3 w l lt 2,\
                    ’ld1.dlog’ u 1:4 w l lt 3, ’ld1ps.dlog’ u 1:2 lt 1, \
                  ’ld1ps.dlog’ u 1:3     lt 2, ’ld1ps.dlog’ u 1:4 lt 3

PS orbitals and the corresponding AE ones are written to file ld1ps.wfc (PS on the
left, AE on the right). They can be plotted using the following commands:

plot [0:5] ’ld1ps.wfc’ u 1:2 lt 1    , ’ld1ps.wfc’ u 1:3 lt 3    , \
           ’ld1ps.wfc’ u 1:4 lt 2    , ’ld1ps.wfc’ u 1:5 lt 1 w l, \
           ’ld1ps.wfc’ u 1:6 lt 3 w l, ’ld1ps.wfc’ u 1:7 lt 2 w l

One gets the following plots (AE=lines, PS=points; lt 1=red=s; lt 2=green=p; lt
3=blue=d; note that in the files, orbitals are ordered as given in input, logarithmic
derivatives as s, p, d).
       20                                                                           1
                                                           ’ld1.dlog’ u 1:2                                             ’ld1ps.wfc’ u 1:2
                                                           ’ld1.dlog’ u 1:3                                             ’ld1ps.wfc’ u 1:3
                                                           ’ld1.dlog’ u 1:4                                             ’ld1ps.wfc’ u 1:4
                                                        ’ld1ps.dlog’ u 1:2                                              ’ld1ps.wfc’ u 1:5
                                                        ’ld1ps.dlog’ u 1:3                                              ’ld1ps.wfc’ u 1:6
       15                                               ’ld1ps.dlog’ u 1:4                                              ’ld1ps.wfc’ u 1:7
                                                                                  0.8




       10
                                                                                  0.6



       5

                                                                                  0.4


       0


                                                                                  0.2

       -5



                                                                                    0
      -10




                                                                                  -0.2
      -15




      -20                                                                         -0.4
            -2   -1.5    -1    -0.5      0   0.5   1          1.5             2          0   1        2     3       4                       5




    We observe that our PP seems to reproduce fairly well the logarithmic derivatives,
with deviations appearing only at relatively high (> 1 Ry) energies. AE and PS orbitals
match very well beyond the pseudization radii; the 3d orbital is slightly deformed,
                                              (l=2)
because we have chosen a relatively large rc        = 1.3 a.u.. It is easy to verify that
            (l=2)
a smaller rc      yields a better 3d PS orbital, but also a harder d potential: e.g., for
 (l=2)
rc     = 1.0 a.u., you get

        Wfc             3D    rcut= 1.009              Estimated cut-off energy=                                225.64 Ry

Before proceding, it is wise to verify whether our PP has “ghosts”. Let us prepare
the following input for the testing phase (note the variable iswitch=2 and the &test
namelist):
```
