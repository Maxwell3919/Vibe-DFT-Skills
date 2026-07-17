# Hubbard_input.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `fe6cde551ed116f5d37af7e838a3b2bed1cbc8eb9efc0ae502b2ed9561c98610`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
U Mn-3d 5.0
J Mn-3d 1.0
B Mn-3d 1.1
U Ni-3d 6.0
J Ni-3d 1.2
B Ni-3d 1.3

If you want to use DFT+U in the Liechtenstein’s formulation (without J) then you still need
to specify some very small value of J (e.g. 1.d-12) so that the automatic algorithm decides
that this is the Liechtenstein’s formulation. If J is not present in the HUBBARD card then the
code will automatically assume that this is DFT+U in the Dudarev’s formulation.

3.3    DFT+U +V (Dudarev’s formulation)
Important notice: The Hubbard U and V values shown in the examples below are random
values chosen just for the sake of demonstration purposes and they must not be used for pro-
duction calculations.

In the past, to use this case the user had to specify in the pw.x input file e.g. the following:

   &system
      ...
      lda_plus_u = .true.
      lda_plus_u_kind = 2
      U_projection_type = ’ortho-atomic’
      Hubbard_V(1,1,1) = 7.70
      Hubbard_V(1,19,1) = 0.75
      Hubbard_V(1,46,1) = 0.75
      Hubbard_V(1,43,1) = 0.75
      Hubbard_V(1,54,1) = 0.75
      Hubbard_V(1,11,1) = 0.75
      Hubbard_V(1,22,1) = 0.75
   /

The meaning of Hubbard V(na,nb,k), where na and nb label atoms as they are specified in
the ATOMIC POSITIONS card (not in the ATOMIC SPECIES card!), and k controls the “interac-
tion type”. When na=nb, Hubbard V(na,na,k) corresponds to Hubbard U(ityp(na)), where
ityp(na) is the atomic type of atom na. The index k could take the following values:

    k=1: interaction between standard orbitals (both on na and nb);

    k=2: interaction between standard (on na) and background (on nb) orbitals;

    k=3: interaction between background orbitals (both on na and nb);

    k=4: interaction between background (on na) and standard (on nb) orbitals.



                                               11
```
