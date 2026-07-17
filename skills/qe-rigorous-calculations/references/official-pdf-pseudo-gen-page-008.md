# pseudo-gen.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `b57c05eef502521f3d1ea14b4362f9cf1feb9662dca9bc3448e2a8e8345d55ff`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
RRKJ method uses three or four Bessel functions for the pseudo-orbitals in the core
region. The former is very robust. The latter may occasionally fail to produce the
required nodeless pseudo-orbital. If this happens, first try to force the usage of four
Bessel functions (this is achieved by setting a small nonzero value of the charge density
at the origin, variable rho0: unfortunately it works only for s states).
    Second-row elements N, O, F, 3d transition metals, rare earths, are typically “hard”
atoms, i.e. described by NC PP’s requiring a high PW cutoff. These atoms are
characterized by 2p (N, O, F), 3d (transition metals), 4f (rare earths) valence states
with no orthogonalization to core states of the same l and no nodes. In addition, as
mentioned in Secs.2.1.2 and 2.1.3, there are case in which you may be forced to include
semicore states in valence, thus making the PP hard (or even harder). In all such
cases, one should consider ultrasoft pseudization, unless there is a good reason to stick
to NC-PP’s. For the specific case of rare earths, however, remember that the problem
of DFT reliability preempts the (tough) problem of generating a PP. With US-PP’s one
can give up the NC requirement and get much softer PP’s, at the price of introducing
an augmentation charge that compensates for the missing charge.
    Currently, the atomic package generates US-PP’s on top of a “hard” NC-PP. In
order to ensure sufficient transferability, at least two states per angular momentum l
are required.

2.2.1   Pseudization energies
If you stick to single-projector PP’s (one potential per angular momentum l, i.e. one
projector per l in the separable form), the choice of the electronic configuration au-
tomatically determines the reference states to pseudize: for each l, the bound valence
eigenstate is pseudized at the corresponding eigenvalue. If no bound valence eigenstate
exists, one has to select a reference energy. The choice is rather arbitrary: you may
try something between than other valence bound state energies and zero.
    If you have semicore states in valence, remember that for each l only the state with
lowest n can be used to generate a single-projector PP. The atomic package requires
that you explicitly specify the configuration for unscreening in the “test” configuration:
see the detailed input documentation.
    It is possible to generate PP’s by pseudizing atomic waves, i.e. regular solutions of
the radial Kohn-Sham equation, at any energy. More than one such atomic waves of
different energy can be pseudized for the same l, resulting in a PP with more than one
projector per l (directly produced in the separable form). Note however that the imple-
mentation of multiple-projector PP’s is correct for US pseudization: NC pseudization
is not properly done (a generalized norm-conservation requirement is not accounted
for). US pseudization is achieved by setting different NC and US pseudization radii
(see Sec.2.2.2),

2.2.2   Pseudization radii
For NC pseudization, one has to choose, for each state to be pseudized, a NC pseudiza-
tion radius rc , at which the AE orbital and the corresponding NC-PP orbital match,
with continuous first derivative at r = rc . For bound states, rc is typically at the
```
