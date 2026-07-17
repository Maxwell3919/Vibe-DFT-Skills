# Hubbard_input.pdf — page 16

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `07bb343be4fd5d612cfe38e92bc67be5bb60747a1a5f98574b7e249b1c030c59`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
relative U parameters, are not transferable and one should not consider U as a universal number
for a given element or material (see the appendix in Ref. [15]). There are other types of Hubbard
projector functions (e.g. truncated atomic orbitals (Abinit), PAW projectors (VASP), etc.),
and the value of U depends on which type of projector functions are used. Therefore, in general
it is not correct to take U from the literature and use it for your DFT+U calculations without
paying attention to what pseudopotentials were used, which Hubbard projector functions, etc.
     During the past 30 years there has been a large effort to develop methods for the first-
principles calculation of U . Among these, the constrained DFT (cDFT) approach, the Hartree-
Fock-based approaches, and the constrained random phase approximation (cRPA) approach
are the most popular. A linear-response formulation of cDFT (LR-cDFT) was introduced in
Ref. [16] and generalized to the calculation of the inter-site Hubbard parameters V in Ref. [12].
Calculation of U and V using LR-cDFT can be done using the pw.x code (see Hubbard alpha
in the pw.x documentation). However, this method requires using supercells which makes
LR-cDFT computationally expensive. Moreover, the postprocessing of the data requires writ-
ing some small programs and/or scripts. Recently, LR-cDFT has been recast via density-
functional perturbation theory (DFPT) [17, 18], allowing us to overcome several challenges of
the supercell approach of Ref. [16]. In fact, by constructing the response of the system to
a localized perturbation through a series of independent monochromatic perturbations to the
primitive unit cell (rather than from finite-differences between calculations in supercells as in
LR-cDFT), it improves significantly the computational efficiency, accuracy, user-friendliness,
and automation. Key to this is indeed the capability to express perturbation theory in reciprocal
space [19, 20, 21]. It is important to mention that the present formulation (be it in a LR-cDFT
or DFPT implementation) aims to correct the over-delocalization and over-hybridization of the
electrons in the localized Hubbard manifold; for this reason it is not appropriate to deal with
closed-shell systems, where the electrons are fully contained in the localized manifold [22].
     The DFPT method for computing Hubbard parameters is implemented in the hp.x code
which is part of the Quantum ESPRESSO distribution. Check the examples in the HP
directory to get started. If you have any questions or problems, please read carefully the
posting guidelines [23] and ask your questions on the QE users forum (users@lists.quantum-
espresso.org).


5    Pseudopotentials
Since Quantum ESPRESSO 7.3.1, the DFT+U codes and its extensions require that pseu-
dopotentials not only contain the atomic orbitals but also the “label” for these orbitals. Most
of the pseudopotential libraries contain “labels” however some do not have them (e.g. pseu-
dopotentials genrated using the ATOMPAW code with versions older than 4.2.0.2):
http://users.wfu.edu/natalie/papers/pwpaw/man.html
    It is possible to fix the pseudopotentials that do not contain the atomic “labels”. To do so,
one has to open the pseudopotential file and look for “PP CHI”. Then simply add the atomic
“label” at the end of the string, e.g. for Gd.GGA-PBESOL-paw.UPF we have

 <PP_CHI.1 type="real" size="1110" l="0" occupation="2.0" columns="3" label="6S">

The orbital quantum number and the occupation of the corresponding level are reported (l=“0”
and occupation=“ 2.0000”) so it is easy to guess that this is the “S” orbital. In order to guess
what is the principal quantum number (n=”6” in this example) one has to check what is

                                               16
```
