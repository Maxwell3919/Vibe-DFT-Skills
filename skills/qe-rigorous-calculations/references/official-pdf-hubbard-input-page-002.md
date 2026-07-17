# Hubbard_input.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `c2b7475425a0841c3ad981796559bb9fce955092e961f46de068b0802cb4bd9f`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
    In 1998 Dudarev and coworkers introduced the rotationally invariant (“simplified”) formu-
lation of DFT+U [3]. In this formulation, instead of having U and J individually we have just
one effective parameter: Ueff = U − J (and often the subscript eff is dropped).
    In 2011 Himmetoglu and coworkers introduced an extension of the Dudarev’s DFT+U
to take into account J in a simplified manner [4]. In order to distinguish from J in the
Liechtenstein’s DFT+U +J, here we use the name “J0 ”. This DFT+U +J0 formulation is not
yet a well-established method and it is an active field of research (see e.g. Refs. [5, 6]).
    One year earlier, in 2010 Campto Jr and Cococcioni extended Dudarev’s formulation of
DFT+U to include inter-site Hubbard V interactions [12]. This is known as the DFT+U +V
approach.
    All the aforementioned methods are implemented in the official Quantum ESPRESSO
7.3.1.


2    Why changing the old input?
In Quantum ESPRESSO 7.0 and earlier, the input parameters for the pw.x code were the
following:

     lda plus u

     lda plus u kind

     Hubbard U

     Hubbard J

     Hubbard J0

     Hubbard V

     U projection type

   Moreover, the Hubbard manifold and the initial atomic occupations were hard-coded in
Modules/set hubbard l.f90 and PW/src/tabd.f90. The data in these routines was far from
being complete. So the user had to modify these routines each time when there were missing
chemical elements and recompile the code. Of course, this was not user friendly especially
when Quantum ESPRESSO was already compiled on some clusters and the user had to ask
system administrators to recompile the code to adapt it to user’s needs.
   In addition, the name lda plus u refers to the old name “LDA+U ”, which is mentioned in
Sec. 1. So this was confusing if e.g. the user want to use GGA (so actually doing GGA+U and
not LDA+U ). The name U projection type again refers to U , but what if we use also J or
V ? So it makes sense to get rid of “U” in the naming and use a generic term “Hubbard” that
covers all cases (DFT+U , DFT+U +J, DFT+U +V , etc.).
   A subgroup of Quantum ESPRESSO developers came up with the idea to try and im-
prove the input syntax in the DFT+Hubbard codes to make it more user-friendly. This new
DFT+Hubbard input syntax replaces the old one starting from Quantum ESPRESSO 7.3.1.




                                             2
```
