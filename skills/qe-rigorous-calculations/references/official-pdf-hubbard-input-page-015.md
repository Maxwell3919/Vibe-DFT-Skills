# Hubbard_input.pdf — page 15

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `e7531f50d015c7a9e17c16d7b9c212475c0f38513f124881d13ad8309394de16`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 &electrons
    conv_thr = 1.d-10
    mixing_beta = 0.7
 /
ATOMIC_SPECIES
 Co 59.0     Co.pbesol-spn-rrkjus_psl.0.3.1.UPF
 O   16.0    O.pbesol-n-rrkjus_psl.0.1.UPF
 Li   7.0    Li.pbesol-s-rrkjus_psl.0.2.1.UPF
ATOMIC_POSITIONS (crystal)
 Co 0.0000000000     0.0000000000   0.0000000000
 O   0.2604885000    0.2604885000   0.2604885000
 O   0.7395115000    0.7395115000   0.7395115000
 Li 0.5000000000     0.5000000000   0.5000000000
K_POINTS (automatic)
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
V Co-3d     Co-3d    1 1 7.70
V Co-3d     Co-3p-3s 1 1 1.00
V Co-3p-3s Co-3p-3s 1 1 2.00
V Co-3p-3s Co-3d     1 1 1.00
V Co-3d     O-2p     1 19 0.75
V Co-3d     O-2s-1s 1 19 0.60
V Co-3p-3s O-2s-1s 1 19 0.50
V Co-3p-3s O-2p      1 19 0.60
...

Note that pseudopotentials for O do not include 1s states. So the example above is just to
show that if you have other elements instead of O and there are more deeper-lying states you
may include them in the “background” channel. As before, it is possible to control the initial
occupations of all these Hubbard manifolds using the keyword Hubbard occ (i.e. if you are not
happy with the initial occupations that are read from pseudopotentials).

Hubbard parameters U and V can be computed using the hp.x code of Quantum ESPRESSO.
However, the hp.x currently supports the calculations of U and V for one Hubbard channel
per atomic type. In other words, the advanced features presented above (i.e. cross-manifold
interactions) are currently not implemented in hp.x.


4    Calculation of Hubbard parameters
In Hubbard-corrected DFT the values of Hubbard parameters are not known a priori. It is a
common practice in literature to evaluate them semi-empirically by fitting various experimental
properties (when available), which prevents this method from being fully ab initio and from
being predictive for novel materials. Most importantly, it is often forgotten that U acts on a
Hubbard manifold that is defined in terms of different Hubbard projector functions such of e.g.
atomic orbitals (atomic) or Löwdin orthogonalized atomic orbitals (ortho-atomic). These are
typically taken from the atomic calculations used to generate the respective pseudopotentials,
that can be constructed with different degrees of oxidation. Hence, these manifolds, and the

                                              15
```
