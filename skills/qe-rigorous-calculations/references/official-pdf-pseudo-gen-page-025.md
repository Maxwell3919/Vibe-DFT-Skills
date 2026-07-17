# pseudo-gen.pdf — page 25

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `7198ae8e8f6b93fe37427f696b39ba881fdc94d8755afe56b99f48997386f260`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
A.4     Numerical solution
The radial (scalar-relativistic) KS equation is integrated on a radial grid. It is conve-
nient to have a denser grid close to the nucleus and a coarser one far away. Traditionally
a logarithmic grid is used: ri = r0 exp(i∆x). With this grid, one has
                              Z ∞            Z ∞
                                   f (r)dr =      f (x)r(x)dx                         (15)
                              0              0

and
                 df (r)   1 df (x)      d2 f (r)       1 df (x)    1 d2 f (x)
                        =          ,              =  −          +             .      (16)
                   dr     r dx           dr2           r2 dx      r2 dx2
We start with a given self-consistent potential V and a trial eigenvalue . The equation
is integrated from r = 0 outwards to rt , the outermost classical (nonrelativistic for
simplicity) turning point, defined by l(l + 1)/rt2 + (V (rt ) − ) = 0. In a logarithmic
grid (see above) the equation to solve becomes:
           1 d2 Rnl (x)
                                                                           
                             1 dRnl (x)       l(l + 1)
                         = 2            +               + M (r) (V (r) − ) Rnl (r)
          r2 dx2             r     dx             r2
                                   α2 dV (r) 1 dRnl (x)
                                                                          
                                                                   Rnl (r)
                             −                               + hκi           .       (17)
                                4M (r) dr          r dx               r
This determines d2 Rnl (x)/dx2 which is used to determine dRnl (x)/dx which in turn
is used to determine Rnl (r), using predictor-corrector or whatever classical integration
method. dV (r)/dr is evaluated numerically from any finite difference method. The
series is started using the known (?) asymptotic behavior of Rnl (r) close to the nucleus
(with ionic charge Z)
                                     √                        p
                                   l   l 2 − α2 Z 2 + (l + 1)  (l + 1)2 − α2 Z 2
              Rnl (r) ≃ rγ ,   γ=                                                .   (18)
                                                        2l + 1
The number of nodes is counted. If there are too few (many) nodes, the trial eigenvalue
is increased (decreased) and the procedure is restarted until the correct number n−l−1
of nodes is reached. Then a second integration is started inward, starting from a
suitably large r ∼ 10rt down to rt , using as a starting point the asymptotic behavior
of Rnl (r) at large r:
                                               r
                                                  l(l + 1)
                   Rnl (r) ≃ e−k(r)r , k(r) =              + (V (r) − ).          (19)
                                                      r2
The two pieces are continuously joined at rt and a correction to the trial eigenvalue
is estimated using perturbation theory (see below). The procedure is iterated to self-
consistency.
    The perturbative estimate of correction to trial eigenvalues is described in the fol-
lowing for the nonrelativistic case (it is not worth to make relativistic corrections on
top of a correction). The trial eigenvector Rnl (r) will have a cusp at rt if the trial
eigenvalue is not a true eigenvalue:
                               dRnl (rt+ ) dRnl (rt− )
                            A=            −            6= 0.                         (20)
                                 dr          dr
```
