# pseudo-gen.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `393c5bbe5e1b5d9e2340b0e77e86eedffe9cadc2df217ce4b28969662310b2aa`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2       Step-by-step Pseudopotential generation
If you want to generate a PP for a given atom, the checklist is the following:

    • choose the generation parameters:

         1. exchange-correlation functional
         2. valence-core partition
         3. electronic reference configuration
         4. nonlinear core correction
         5. type of pseudization
         6. pseudization energies
         7. pseudization radii
         8. local potential

    • generate the pseudopotential

    • check for transferability

In case of trouble or of unsatisfactory results, one has to go back to the first step and
change the generation parameters, usually in the last four items.

2.1     Choosing the generation parameters
2.1.1    Exchange-correlation functional
PP’s must be generated with the same exchange-correlation (XC) functional that will
be later used in calculations. The use of, for instance, a GGA (Generalized Gradient
Approximation) functional tegether with PP’s generated with Local-Density Approx-
imation (LDA) is inconsistent. This is why the PP file contains information on the
DFT level used in their generation: if you or your code ignore it, you do it at your own
risk.
    The atomic package allows PP generation for a large number of functionals, both
LDA and GGA. Most of them have been extensively tested, but beware: some exotic
or seldom-used functionals might contain bugs. Currently, atomic does not allow PP
generation with meta-GGA (TPSS) or hybrid functionals. For the former, an old
version of atomic, modified by Xiaofei Wang, is available. Work is in progress for the
latter.
    Some functionals may present numerical problems when the charge density goes
to zero. For instance, the Becke gradient correction to the exchange may diverge for
ρ → 0. This does not happen in a free atom if the charge density behaves as it should,
that is, as ρ(r) → exp(−αr) for r → ∞. In a pseudoatom, however, a weird behavior
may arise around the core region, r → 0, because the pseudocharge in that region is very
small or sometimes vanishing (if there are no filled s states). As a consequence, nasty-
looking “spikes” appear in the unscreened pseudopotential very close to the nucleus.
This is not nice at all but it is usually harmless, because the interested region is really
```
