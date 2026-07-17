# brillouin_zones.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/brillouin_zones.pdf
- Retrieved: 2026-07-17T11:53:22+00:00
- Official source SHA-256: `debca2c4482e2488b38a4cef3ff92bff200bf2aa4f316d0ad45abe859d5fc0aa`
- Extracted text SHA-256: `b19599ffe527a353d21c8a724178ebdd0acf1f5a9bba7eeed4c5f671e469972e`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
1.5    ibrav=5, trigonal lattice
The primitive vectors of the direct lattice are:
                                        √
                                          3          1
                             a1 = a(        sin θ, − sin θ, cos θ),
                                         2           2
                             a2 = a(0, sin θ, cos θ),
                                          √
                                            3          1
                             a3 = a(−         sin θ, − sin θ, cos θ),
                                           2           2

while the reciprocal lattice vectors are:
                                   2π       1          1        1
                            b1 =      (√         ,−         ,       ),
                                    a     3 sin θ 3 sin θ 3 cos θ
                                   2π         2      1
                            b2   =    (0,        ,        ),
                                    a     3 sin θ 3 cos θ
                                   2π          1         1        1
                            b3   =    (− √         ,−         ,        ),
                                    a       3 sin θ 3 sin θ 3 cos θ
                                                                                        (1)
              q √                           q √
                 2
where sin θ =    3
                    1 − cos α and cos θ = 13 1 + 2 cos α and α is the angle between any two
primitive direct lattice vectors. There are two possible shapes of the BZ, depending on the
value of the angle α. For α < 90◦ we have:




The figure has been obtained with α = 70◦ . For 90◦ < α < 120◦ we have:




                                                  6
```
