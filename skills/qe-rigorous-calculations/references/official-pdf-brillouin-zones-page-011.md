# brillouin_zones.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/brillouin_zones.pdf
- Retrieved: 2026-07-17T11:53:22+00:00
- Official source SHA-256: `debca2c4482e2488b38a4cef3ff92bff200bf2aa4f316d0ad45abe859d5fc0aa`
- Extracted text SHA-256: `13bb576910b80674c71e965f6cbeb4397989857306b022d006a903d7b3144f8c`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
In this case there are three different shapes that can be rotated in different ways depending
on the relative sizes of a, b, and c. If a is the shortest side, there are three different shapes
according to
                                            1     1    1
                                             2
                                               ⪋ 2 + 2,                                       (2)
                                           a      b    c
if b is the shortest side there are three different shapes according to
                                          1    1   1
                                             ⪋   +    ,                                        (3)
                                          b2   a2 c 2
and if c is the shortest side there are three different shapes according to
                                          1    1   1
                                             ⪋   +    .                                        (4)
                                          c2   a2 b 2
For each case there are two possibilities. If a is the shortest side, we can have b < c or b > c,
if b is the shortest side, we can have a < c or a > c, and finally if c is the shortest side we can
have a < b or a > b. In total we have 18 distinct cases. Not all cases give different BZ. All the
cases with the < sign in Eqs. 2, 3, 4 give the same shape of the BZ that differ for the relative
sizes of the faces. All the cases with the > sign in Eqs. 2, 3, 4 give the same shape with faces
of different sizes and oriented in different ways. Finally the particular case with the = sign in
Eqs. 2, 3, 4 give another shape with faces of different size and different orientations. We show
all the 18 possibilities and the labels used in each case.
    We start with the case in which a is the shortest side and show on the left the case b < c
and on the right the case b > c. The first possibility is that a12 < b12 + c12 :




The figures have been obtained with b/a = 1.2 and c/a = 1.4 (left part b < c), and with
b/a = 1.4 and c/a = 1.2 (right part b > c).
   The second possibility is that a12 = b12 + c12 :




                                                11
```
