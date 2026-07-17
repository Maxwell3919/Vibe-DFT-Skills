# pseudo-gen.pdf — page 3

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `06f19b792382d2fa8bf03339d55e538186013d7bc8b2cac06cdb835540f29458`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
1.2    About similar work
There are other PP generation packages available on-line. Those I am aware of include:

   • the code by José-Luı́s Martins et al.[7]:
     http://bohr.inesc-mn.pt/~jlm/pseudo.html

   • the fhi98PP package[8]:
     http://www.fhi-berlin.mpg.de/th/fhi98md/fhi98PP

   • the OPIUM code by Andrew Rappe et al.[9]:
     http://opium.sourceforge.net/

   • David Vanderbilt’s US-PP package [2]:
     http://www.physics.rutgers.edu/~dhv/uspp/index.html.

Other codes may be available upon request from the authors.
    Years ago, it occurred to me that a web-based PP generation tool would have been
nice. Being too lazy and too ignorant in web-based applications, I did nothing. I
recently discovered that Miguel Marques et al. have implemented something like this:
see http://www.tddft.org/programs/octopus/pseudo.php.

1.3    Pseudopotential generation, in general
In the following I am assuming that the basic PP theory is known to the reader.
Otherwise, see Refs.[1, 4, 7, 8, 9] and references quoted therein for NC-PP’s; Refs.[2, 3]
for US-PP’s and PAWsets. I am also assuming that the generated PP’s are to be used
in separable form [10] with a plane-wave (PW) basis set.
    The PP generation is a three-step process. First, one generates atomic levels and
orbitals with Density-functional theory (DFT). Second, from atomic results one gener-
ates the PP. Third, one checks whether the reesulting PP is actually working. If not,
one tries again in a different way.
    The first step is invariably done assuming a spherically symmetric self-consistent
Hamiltonian, so that all elementary quantum mechanics results for the atom apply. The
atomic state is defined by the ”electronic configuration”, one-electron states are defined
by a principal quantum number and by the angular momentum and are obtained by
solving a self-consistent radial Schrödinger-like (Kohn-Sham) equation.
    The second step exists in many variants. One can generate “traditional” single-
projector NC-PP’s; multiple-projector US-PP’s, or PAW sets. The crucial step is in
all cases the generation of smooth “pseudo-orbitals” from atomic all-electron (AE)
orbitals. Two popular pseudization methods are presently implemented: Troullier-
Martins [7] and Rappe-Rabe-Kaxiras-Joannopoulos [9] (RRKJ).
    The second and third steps are closer to cooking than to science. There is a large
arbitrariness in the preceding step that one would like to exploit in order to get the
”best” PP, but there is no well-defined way to do this. Moreover one is often forced to
strike a compromise between transferability (thus accuracy) and hardness (i.e. com-
puter time). These two steps are the main focus of these notes.
```
