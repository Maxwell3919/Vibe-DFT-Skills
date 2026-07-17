# pseudo-gen.pdf — page 24

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `dd96f559a75b2b3f187e0ab2d0a69d27361a7e83c1da8a618549c2d82902ab0e`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
A.1.1    Useful formulae
Gradient in spherical coordinates (r, θ, φ):
                                                      
                                      ∂ψ 1 ∂ψ   1 ∂ψ
                            ∇ψ =          ,   ,                                               (7)
                                      ∂r r ∂θ rsinθ ∂φ
Laplacian in spherical coordinates:
                    1 ∂2                                                         1 ∂ 2ψ
                                                                    
                  2                 1 ∂                        ∂ψ
                ∇ψ=        (rψ) + 2                       sinθ           +                    (8)
                    r ∂r 2       r sinθ ∂θ                     ∂θ            r2 sin2 θ ∂φ2

A.2     Fully relativistic case
The relativistic KS equations are Dirac-like equations for a spinor with a “large” Rnlj (r)
and a “small” Snlj (r) component:
                            
                      d    κ
                               Rnlj (r) = 2mc2 − V (r) +  Snlj (r)
                                                               
                  c      +                                                              (9)
                      dr r
                            
                       d   κ
                  c      −     Snlj (r) = (V (r) + ) Rnlj (r)                       (10)
                      dr r
where j is the total angular momentum (j = 1/2 if l = 0, j = l+1/2, l−1/2 otherwise);
κ = −2(j − l)(j + 1/2) is the Dirac quantum number (κ = −1 is l = 0, κ = −l − 1, l
otherwise); and the charge density is given by
                                                   2           2
                                     X            Rnlj (r) + Snlj (r)
                            n(r) =         Θnlj              2
                                                                      .                      (11)
                                     nlj
                                                         4πr


A.3     Scalar-relativistic case
The full relativistic KS equations is be transformed into an equation for the large
component only and averaged over spin-orbit components. In atomic units (Rydberg:
~ = 1, m = 1/2, e2 = 2):

                d2 Rnl (r)
                                                          
                               l(l + 1)
              −            +            + M (r) (V (r) − ) Rnl (r)
                   dr2             r2
                              α2 dV (r) dRnl (r)
                                                                  
                                                           Rnl (r)
                         −                           + hκi           = 0,      (12)
                            4M (r) dr         dr             r
where α = 1/137.036 is the fine-structure constant, hκi = −1 is the degeneracy-
weighted average value of the Dirac’s κ for the two spin-orbit-split levels, M (r) is
defined as
                                          α2
                             M (r) = 1 −     (V (r) − ) .                      (13)
                                           4
The charge density is defined as in the nonrelativistic case:
                                                          2
                                            X            Rnl (r)
                                 n(r) =            Θnl           .                           (14)
                                             nl
                                                         4πr2
```
