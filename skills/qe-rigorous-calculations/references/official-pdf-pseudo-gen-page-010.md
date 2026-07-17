# pseudo-gen.pdf — page 10

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `7806ea18479051544a93a7355ab41cf7625e662a98065938ee85761187819fc9`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
to problems, and one is forced to use a different l. Another possibility is to generate a
local potential by pseudizing the AE potential.
    Note that ghosts may not be visible to atomic codes based on radial integration,
since the algorithm discards states with the wrong number of nodes. Difficult conver-
gence or mysterious errors are almost invariably a sign tha there is something wrong
with our PP. A simple and safe way to check for the presence of a ghost is to diagonalize
the Kohn-Sham hamiltonian in a basis set of spherical Bessel functions. This can be
done together with transferability tests (see Sec.2.4)

2.3    Generating the pseudopotential
As a first step, one can generate AE Kohn-Sham orbitals and one-electron levels for
the reference configuration. This is done by using executable ld1.x. You must specify
in the input data:

      atomic symbol,
      electronic reference configuration,
      exchange-correlation functional (default is LDA).

A complete description of the input is contained in the documentation. For accurate
AE results in heavy atoms, you may want to specify a denser radial grid in r-space than
the default one. The default grid should however be good enough for PP generation.
   Before you proceed, it is a good idea to verify that the atomic data you just produced
actually make sense. Some kind souls have posted on the web a complete set of reference
atomic data :

      http://physics.nist.gov/PhysRefData/DFTdata/

These data have been obtained with the Vosko-Wilk-Nusair functional, that for the
unpolarized case is very similar to the Perdew-Zunger LDA functional (this is hte LDA
default).
   The generation step is also done by program ld1.x. One has to supply, in addition
to AE data:

      a list of orbitals to be pseudized, with pseudization energies and radii,
      the filename where the newly generated PP is written,

plus a number of other optional parameters, fully described in the documentation.

2.4    Checking for transferability
A simple way to check for correctness and to get a feeling for the transferability of a
PP, with little effort, is to test the results of PP and AE atomic calculations on atomic
configurations differing from the starting one. The error on total energy differences
between PP and AE results gives a feeling on how good the PP is. Just to give an
idea: an error ∼ 0.001 Ry is very good, ∼ 0.01 Ry may still be acceptable. The code
ld1.x has a “testing” mode in which it does exactly the above operation. You provide
the input PP file and a number of test configurations.
```
