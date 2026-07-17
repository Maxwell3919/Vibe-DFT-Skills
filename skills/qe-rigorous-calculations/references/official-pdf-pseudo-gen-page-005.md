# pseudo-gen.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `c297756c3ceca1396c93121964ccd58bfff4268c933482b3ee9067d33f5c9ac0`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
very small. However in some unfortunate cases there can be convergence problems. If
you do not want to see those horrible spikes, or if you experience problems, you have
the following choices:

   – Use a better-behaved GGA, such as PBE

   – Use the nonlinear core correction, which ensures the presence of some charge
     close to the nucleus.

A further possibility would be to cut the gradient correction for small r (it used to be
implemented, but it isn’t any longer).

2.1.2   Valence-core partition
This seems to be a trivial step, and often it is: valence states are those that contribute
to bonding, core states are those that do not contribute. Things may sometimes be
more complicated than this. For instance:

   – in transition metals, whose typical outer electronic configuration is something
     like (n = main quantum number) ndi (n + 1)sj (n + 1)pk , it is not always evident
     that the ns and np states (“semicore states”) can be safely put into the core.
     The problem is that nd states are localized in the same spatial region as ns and
     np states, deeper than (n + 1)s and (n + 1)p states. This may lead to poor
     transferability. Typically, PP’s with semicore states in the core work well in
     solids with weak or metallic bonding, but perform poorly in compounds with a
     stronger (chemical) type of bonding.

   – Heavy alkali metals (Rb, Cs, maybe also K) have a large polarizable core. PP’s
     with just one electron may not always give satisfactory results.

   – In some II-VI and III-V semiconductors, such as ZnSe and GaN, the contribution
     of the d states of the cation to the bonding is not negligible and may require
     explicit inclusion of those d states into the valence.

In all these cases, promoting the highest core states ns and np, or nd, into valence may
be a computationally expensive but obliged way to improve poor transferability. .
    You should include semicore states into valence only if really needed: their inclusion
in fact makes your PP harder (unless you resort to US pseudization) and increases the
number of electrons. In principle you should also use more than one projector per
angular momentum, because the energy range to be covered by the PP with semicore
electrons is much wider than without. For instance, it may happen that the error
on the lattice parameter of a simple metal is larger with a semicore PP than with a
valence-only PP.

2.1.3   Electronic reference configuration
This may be any reasonable configuration not too far away from the expected configu-
ration in solids or molecules. As a first choice, use the atomic ground state, unless you
have a reason to do otherwise, such as for instance:
```
