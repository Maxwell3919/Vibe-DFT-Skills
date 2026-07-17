# pseudo-gen.pdf — page 9

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `95b160aa8df2ad409f4f030198ea28a0ba40118a3419fc2c1f81ba26b86f711a`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
outermost peak or somewhat larger. The larger the rc , the softer the potential (less
PW needed in the calculations), but also the less transferable. The rc may differ for
different l; as a rule, one should avoid large differences between the rc ’s, but this is not
always possible. Also, the rc cannot be smaller than the outermost node.
     A big problem in NC-PP’s is how strike a compromise between softness and trans-
ferability, especially for difficult elements. The basic question: “how much should I
push rc outwards in order to have reasonable results with a reasonable PW cutoff”.
has no clear-cut answer. The choice of rc at the outermost maximum for “difficult”
elements (those described in Sec.2.2.1): typically 0.7-0.8 a.u, even less for 4f electrons,
yields very hard PP’s (more than 100 Ry needed in practical calculations). With a
little bit of experience one can say that for second-row (2p) elements, rc = 1.1 − 1.2 will
yield reasonably good results for 50-70 Ry PW kinetic energy cutoff; for 3d transition
metals, the same rc will require > 80 Ry cutoff (highest l have slower convergence for
the same rc ). The above estimates are for TM pseudization. RRKJ pseudization will
yield an estimate of the required cutoff.
     For multiple-projectors PP’s, the rc of unbound states may be chosen in the same
range as for bound states. Use small rc and don’t try to push them outwards: the
US pseudization will take care of softness. US pseudization radii can be chosen much
larger than NC ones (e.g. 1.3÷ 1.5 a.u. for second-row 2p elements, 1.7÷ 2.2 a.u. for
3d transition metals), but do not forget that the sum of the rc of two atoms should not
exceed the typical bond length of those atoms.
     Note that it is the hardest atom that determines the PW cutoff in a solid or
molecule. Do not waste time trying to find optimally soft PP’s for element X if element
Y is harder then element X.

2.2.3   Choosing the local potential
As explained in Sec. 2.1.3, note 1, one needs in principle angular momentum channels
in PP’s up to lc + 1. In the semilocal form, the choice of a ”local”, l-independent
potential is natural and affects only seldom-important PW components with l > lc .
In PW calculations, however, a separable, fully nonlocal form – one in which the
PP’s is written as a local potential plus pr ojectors – is used. An arbitrary function
can be added to the local potential and subtracted to all l components. Generally
one exploits this arbitrariness to remove one l component using it as local potential.
The separable form can be either obtained by the Kleinman-Bylander projection [10]
applied to single-projector PP’s, or directly produced using Vanderbilt’s procedure [2]
(for single-projector PP’s the two approaches are equivalent).
    Unfortunately the separable form is not guaranteed to have the correct ground state
(unlike the semilocal form, which, by construction, has the correct ground states):
“ghost” states, having the wrong number of nodes, can appear among the occupied
states or close to them, making the PP completely useless. This problem may show up
in US-PP’s as well.
    The freedom in choosing the local part can (and usually must) be used in order to
avoid the appearance of ghosts. For PW calculations it is convenient to choose as local
part the highest l, because this removes more projectors (2l + 1 per atom) than for
low l. According to Murphy’s law, this is also the choice that more often gives raise
```
