# pseudo-gen.pdf — page 26

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `b11d066f11d117f5cb09660807a3729bef97cc81fda781180e509dc24c2ee718`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Such discontinuity in the first derivative translates into a δ(rt ) in the second derivative:

                            d2 Rnl (r)   d2 R
                                            enl (r)
                                       =            + Aδ(r − rt )                       (21)
                               dr2          dr2
where the tilde denotes the function obtained by matching the second derivatives in
the r < rt and r > rt regions. This means that we are actually solving a different
problem in which V (r) is replaced by V (r) + ∆V (r), given by

                                            ~2   A
                             ∆V (r) = −                  δ(r − rt ).                    (22)
                                            2m Rnl (rt )
The energy difference between the solution to such fictitious potential and the solution
to the real potential can be estimated from perturbation theory:
                                                       ~2
                           ∆nl = −hψ|∆V |ψi =            Rnl (rt )A.                   (23)
                                                       2m

B       Equations for the Troullier-Martins method
We assume a pseudowavefunction Rps having the following form:

                               Rps (r) = rl+1 ep(r) r ≤ rc                              (24)
                               Rps (r) = R(r) r ≥ rc                                    (25)

where
                 p(r) = c0 + c2 r2 + c4 r4 + c6 r6 + c8 r8 + c10 r10 + c12 r12 .        (26)
On this pseudowavefunction we impose the norm conservation condition:
                        Z                 Z
                               ps   2
                            (R (r)) dr =      (R(r))2 dr                                (27)
                              r<rc                    r<rc

and continuity conditions on the wavefunction and its derivatives up to order four at
the matching point:
                         dn Rps (rc )   dn R(rc )
                                      =           , n = 0, ..., 4                (28)
                            drn           drn
• Continuity of the wavefunction:

                                Rps (rc ) = rcl+1 ep(rc ) = R(rc )                      (29)
                                                     R(rc )
                                      p(rc ) = log                                      (30)
                                                     rcl+1
• Continuity of the first derivative of the wavefunction:
          dRps (r)                                         l + 1 ps
                   = (l + 1)rl ep(r) + rl+1 ep(r) p0 (r) =      R (r) + p0 (r)Rps (r)   (31)
            dr                                               r
that is
                                          dR(rc ) 1      l+1
                             p0 (rc ) =           ps
                                                       −     .                          (32)
                                            dr R (rc )    rc
```
