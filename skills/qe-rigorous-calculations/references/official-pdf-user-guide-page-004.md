# user_guide.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `9138b5093fd579ed5e3655503cdbd6f68d7bc0088ce92e8f18f52fa8be6a35d5`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
This guide does not explain the basic Unix concepts (shell, execution path, directories etc.) and
utilities needed to run Quantum ESPRESSO; it does not explain either solid state physics
and its computational methods. If you want to learn the latter, you should first read a good
textbook, such as e.g. the book by Richard Martin: Electronic Structure: Basic Theory and
Practical Methods, Cambridge University Press (2004); or: Density functional theory: a prac-
tical introduction, D. S. Sholl, J. A. Steckel (Wiley, 2009); or Electronic Structure Calculations
for Solids and Molecules: Theory and Computational Methods, J. Kohanoff (Cambridge Uni-
versity Press, 2006). Then you should consult the documentation of the package you want to
use for more specific references.
    All trademarks mentioned in this guide belong to their respective owners.

1.1    People
The maintenance and further development of the Quantum ESPRESSO distribution is pro-
moted by the Quantum ESPRESSO Foundation under the coordination of Paolo Giannozzi
(Univ. Udine and IOM-CNR, Italy) and Pietro Delugas (SISSA Trieste) with a strong support
from the MaX - Materials design at the Exascale EU Centre of Excellence and from the CINECA
computing centre. The NVidia GPU porting owes much to Pietro Bonfà (Univ. Modena), Ivan
Carnimeo (SISSA Trieste), Fabrizio Ferrari Ruffino (IOM-CNR).
   Contributors to Quantum ESPRESSO, beyond the authors of the papers mentioned in
Sec.1.4, include:

   • Ye Luo (Argonne) for many contributions to CMake maintenance, improved threading,
     GPU porting, CI (Continuous integration), testing;

   • Laura Bellentani (CINECA) for GPU porting, optimization and benchmarking;

   • Fabio Affinito and Sergio Orlandini (CINECA) for ELPA support, for contributions to
     the FFT library, and for various parallelization improvements;

   • Victor Yu (Urbana-Champaign) for various bug fixes and optimizations;

   • Alexandre Tkatchenko’s group, in particular Szabolcs Goger (U. Luxembourg), and Robert
     DiStasio’s group, in particular Hsin-Yu Ko (Cornell), for Many-Body Dispersion (MBD)
     correction;

   • Federico Ficarelli and Daniele Cesarini (CINECA), with help from Ye Luo (Argonne) and
     Sebastian Gsänger, for CMake support;

   • Sebastiano Caravati for direct support of GTH pseudopotentials in analytical form, San-
     tana Saha and Stefan Goedecker (Basel U.) for improved UPF converter of newer GTH
     pseudopotentials;

   • Axel Kohlmeyer for libraries and utilities to call Quantum ESPRESSO from external
     codes (see the COUPLE sub-directory), made the parallelization more modular and usable
     by external codes;

   • Èric Germaneau for TB09 meta-GGA functional, using libxc;

   • Guido Roma (CEA Saclay) for vdw-df-obk8 e vdw-df-ob86 functionals;


                                                4
```
