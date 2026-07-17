# pseudo-gen.pdf — page 27

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `561a6af8bb8b97402e4e82610b2d3f1d7e856f050445575fe7179912843e71d3`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
• Continuity of the second derivative of the wavefunction:

 d2 Rps (r)    d            l p(r)     l+1 p(r) 0
                                                      
            =      (l + 1)r  e     + r    e    p  (r)
    d2 r      dr
                                                                                2
            = l(l + 1)rl−1 ep(r) + 2(l + 1)rl ep(r) p0 (r) + rl+1 ep(r) [p0 (r)] + rl+1 ep(r) p00 (r)
                                                                
                l(l + 1) 2(l + 1) 0                0    2   00
            =            +            p (r) + [p (r)] + p (r) rl+1 ep(r) .                       (33)
                    r2           r

From the radial Schrödinger equation:

                   d2 Rps (r)
                                                        
                                  l(l + 1) 2m
                              =           + 2 (V (r) − ) Rps (r)                                 (34)
                      dr2             r2   ~

that is
                            2m                    l+1 0                   2
                      p00 (rc ) =
                              2
                                (V (rc ) − ) − 2     p (rc ) − [p0 (rc )]         (35)
                             ~                     rc
• Continuity of the third and fourth derivatives of the wavefunction. This is assured
if the third and fourth derivatives of p(r) are continuous. By direct derivation of the
expression of p00 (r):

                           2m 0           l+1 0             l + 1 00
            p000 (rc ) =      V (rc ) + 2      p (r c ) − 2      p (rc ) − 2p0 (rc )p00 (rc )     (36)
                           ~2              rc2                rc


                               2m 00           l+1 0               l + 1 00
              p0000 (rc ) =       V  (rc ) − 4       p (r c ) + 4          p (r)
                               ~2                rc3                 rc2
                                  l + 1 000                              2
                               −2        p (rc ) − 2 [p00 (rc )p00 (rc )] − 2p0 (rc )p000 (rc )   (37)
                                    rc
   The additional condition: V 00 (0) = 0 is imposed. The screened potential is

                             ~2        1 d2 Rps (r) l(l + 1)
                                                               
                 V (r) =                             −            +                              (38)
                            2m Rps (r) dr2                r2
                             ~2
                                                                
                                      l+1 0             2    00
                        =           2     p (r) + [p(r)] + p (r) +                               (39)
                            2m         r

   Keeping only lower-order terms in r:

                    ~2
                                                                         
                            l+1                3      2 2               2
         V (r) ≃          2      (2c2 r + 4c4 r ) + 4c2 r + 2c2 + 12c4 r +                       (40)
                    2m        r
                    ~2
                         2c2 (2l + 3) + (2l + 5)c4 + c22 r2 + .
                                                           
                =                                                                                 (41)
                    2m
The additional constraint is:
                                          (2l + 5)c4 + c22 = 0.                                   (42)
```
