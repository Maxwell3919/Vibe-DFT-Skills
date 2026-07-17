# pseudo-gen.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `c9efeb3fe618a81af7c9d71a5e49adcfe128a82afe5b1fd36abcc1348baf9804`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   – You do not want to deal with unbound states. Very often states with highest
     angular momentum l are not bound in the atom (an example: the 3d state in Si
     is not bound on the ground state 3s2 3p2 , at least with LDA or GGA). In such a
     case one has the choice between

        – using one configuration for s and p, another, more ionic one, for d, as in
          Refs.[4, 5];
        – choosing a single, more ionic configuration for which all desired states are
          bound;
        – generate PP’s on unbound states: requires to choose a suitable reference
          energy.

   – The results of your PP are very sensitive to the chosen configuration. This is
     something that in principle should not happen, but I am aware of at least one
     case in which it does. In III-V zincblende semiconductors, the equilibrium lattice
     parameter is rather sensitive to the form of the d potential of the cation (due to
     the presence of p − d coupling between anion p states and cation d states [12]).
     By varying the reference configuration, one can change the equilibrium lattice
     parameter by as much as 1 − 2%. The problem arises if you want to calculate
     accurate dynamical properties of GaAs/AlAs alloys and superlattices: you need
     to get a good theoretical lattice matching between GaAs and AlAs, or otherwise
     unpleasant spurious effects may arise. When I was confronted with this problem,
     I didn’t find any better solution than to tweak the 4d reference configuration for
     Ga until I got the observed lattice-matching.

   – You know that for the system you are interested in, the atom will be in a given
     configuration and you try to stay close to it. This is not very elegant but some-
     times it is needed. For instance, in transition metals described by a PP with
     semicore states in the core, it is probably wise to chose an electronic configura-
     tion for d states that is close to what you expect in your system (as a hand-waiving
     argument, consider that the (n + 1)s and (n + 1)p PP have a hard time in repro-
     ducing the true potential if the nd state, which is much more localized, changes a
     lot with respect to the starting configuration). In Rare-Earth compounds, leav-
     ing the 4f electrons in the core with the correct occupancy (if known) may be a
     quick and dirty way to avoid the well-known problems of DFT yielding the wrong
     occupancy in highly correlated materials.

   – You don’t manage to build a decent PP with the ground state configuration, for
     whatever reason.

    NOTE 1: you can calculate PP for a l as high as you want, but you are not obliged
to use all of them in PW calculations. The general rule is that if your atom has states
up to l = lc in the core, you need a PP with angular momenta up to l = lc + 1. Angular
momenta l > lc +1 will feel the same potential as l = lc +1, because for all of them there
is no orthogonalization to core states. As a consequence a PP should have projectors
on angular momenta up to lc ; l = lc + 1 should be the local reference state for PW
calculations. This rule is not very strict and may be relaxed: high angular momenta
```
