# pseudo-gen.pdf — page 23

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `41c2b9f7113daed7240ba70041b185405484f2e4d3e0f57ccf7b1df63e9acf65`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
3.3    Testing in molecules and solids
Even if our PP looks good (or not too bad) on paper based on the results of atomic
calculations, it is always a good idea to test it in simple molecular or solid-state systems,
for which all-electron data (i.e. calculations performed with the same XC functional
but without PP’s, such as e.g. FLAPW, LMTO, Quantum Chemistry calculations) is
available. The comparison with experiments is of course interesting, but the goal of
PP’s is (at least in principle) to reproduce AE data, not to improve DFT.


A      Atomic Calculations
A.1     Nonrelativistic case
Let us assume that the charge density n(r) and the potential V (r) are spherically
symmetric. The Kohn-Sham (KS) equation:
                            ~2 2
                                            
                          −    ∇ + V (r) −  ψ(r) = 0                          (1)
                            2m
can be written in spherical coordinates. We write the wavefunctions as
                                               
                                        Rnl (r)
                               ψ(r) =             Ylm (r̂),                               (2)
                                          r
where n is the main quantum number l = n − 1, n − 2, . . . , 0 is angular momentum,
m = l, l − 1, . . . , −l + 1, −l is the projection of the angular momentum on some axis.
The radial KS equation becomes:
           ~2 1 d2 Rnl (r)
                                                   
                                           1
         −                    + (V (r) − ) Rnl (r) Ylm (r̂)
           2m r dr2                        r
                    2
                                                       1 ∂ 2 Ylm (r̂) 1
                                                                  
                 ~        1 ∂          ∂Ylm (r̂)
            −                     sinθ             +                      Rnl (r) = 0. (3)
                2m sinθ ∂θ               ∂θ          sin2 θ ∂φ2        r3
This yields an angular equation for the spherical harmonics Ylm (r̂):
                                              1 ∂ 2 Ylm (r̂)
                                                          
                  1 ∂         ∂Ylm (r̂)
            −            sinθ             +                    = l(l + 1)Ylm (r̂)         (4)
                sinθ ∂θ         ∂θ          sin2 θ ∂φ2
and a radial equation for the radial part Rnl (r):
                  ~2 d2 Rnl (r)
                                   2                      
                                    ~ l(l + 1)
               −                +               + V (r) −  Rnl (r) = 0.                  (5)
                 2m dr2            2m r2
The charge density is given by
                                                             2                   2
                              X           Rnl (r)                    X          Rnl (r)
                     n(r) =         Θnl           Ylm (r̂)       =        Θnl             (6)
                              nlm
                                            r                        nl
                                                                                4πr2

where Θnl are the occupancies (Θnl ≤ 2l + 1) and it is assumed that the occupancies
of m are such as to yield a spherically symmetric charge density (which is true only for
closed shell atoms).
```
