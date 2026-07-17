# ph_user_guide.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/ph_user_guide.pdf
- Retrieved: 2026-07-17T11:53:35+00:00
- Official source SHA-256: `aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60`
- Extracted text SHA-256: `048ea0aef814dfbb44600904512eab876ee697d7db164f6205973f908ba9c1f7`
- Official Last-Modified: Mon, 08 Dec 2025 21:32:34 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
4.8    Fourier interpolation of phonon potential
The potential perturbation caused by the displacement of a single atom is spatially localized.
Hence, the phonon potential can be interpolated from q points on a coarse grid to other q points
using Fourier interpolation. To use this functionality, first, one shoud run a ph.x calculation
for q points on a regular coarse grid. Then, a dvscf q2r.x run performs an inverse Fourier
transformation of the phonon potentials from a q grid to a real-space supercell. Finally, by spec-
ifying ldvscf interpolation=.true. in ph.x, the phonon potentials are Fourier transformed
to given q points.
    For insulators, the nonanalytic long-ranged dipole part of the potential needs to be sub-
tracted and added before and after the interpolation, respectively. This treatment is activated
by specifying do long range=.true. in the input files of dvscf q2r.x and ph.x.
    Due to numerical inaccuracies, the calculated Born effective charges may not add up to zero,
violating the charge neutrality condition. This error may lead to nonphysical polar divergence
of the phonon potential for q points close to Γ, even in IR-inactive materials. To avoid this
problem, one can specify do charge neutral=.true. in the input files of dvscf q2r.x and
ph.x. Then, the phonon potentials and the Born effective charges are renormalized by enforcing
the charge neutrality condition, following the scheme of S. Ponce et al, J. Chem. Phys. (2015).
    The Fourier interpolation of phonon potential is proposed and described in the following
papers:
    A. Eiguren and C. Ambrosch-Draxl, Phys. Rev. B 78, 045124 (2008);
    S. Ponce et al, J. Chem. Phys. 143, 102813 (2015);
    X. Gonze et al, Comput. Phys. Commun., 248, 107042 (2020).

4.9    Calculation of phonon-renormalization of electron bands
The phonon-induced renormalization of electron bands can be computed using PHonon. After
SCF, PHONON, and NSCF calculations, one can run ph.x with the electron phonon=‘ahc’
option, which generates binary files containing quantities required for the calculation of electron
self-energy. Then, a postahc.x run reads these binary files and compute the phonon-induced
electron self-energy at a given temperature.
    For more details, see the PHonon/Doc/dfpt_self_energy.pdf file.
    Also, there is an example in PHonon/example/example19/.
    Implementation of this functionality in Quantum ESPRESSO is described in the following
paper:
    J.-M. Lihm and C.-H. Park, Phys. Rev. B 101, 121102 (2020).


5     Parallelism
We refer to the corresponding section of the PWscf guide for an explanation of how parallelism
works.
   ph.x may take advantage of MPI parallelization on images, plane waves (PW) and on k-
points (“pools”). Currently all other MPI and explicit OpenMP parallelizations have very
limited to nonexistent implementation. phcg.x implements only PW parallelization. All other
codes may be launched in parallel, but will execute on a single processor.
   In “image” parallelization, processors can be divided into different “images”, corresponding
to one (or more than one) “irrep” or q vectors. Images are loosely coupled: processors com-

                                                8
```
