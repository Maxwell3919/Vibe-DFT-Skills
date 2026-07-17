# Hubbard_input.pdf — page 9

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `b9dabe3f0203409543e1d8a8f0b517642dc777639cae028ed4cbd656a03af473`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 Ni 58.693 Ni.pbesol-n-rrkjus_psl.0.1.UPF
 Ga 69.723 Ga.pbesol-dn-rrkjus_psl.0.2.UPF
ATOMIC_POSITIONS (crystal)
 Mn 0.0000000000   0.0000000000 0.0000000000
 Ni 0.5000000000   0.7500000000 0.2500000000
 Ni 0.5000000000   0.2500000000 0.7500000000
 Ga 0.0000000000   0.5000000000 0.5000000000
K_POINTS (automatic)
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
U Mn-3d 5.0
J0 Mn-3d 1.0
U Ni-3d 6.0
J0 Ni-3d 1.2

In the example above we apply Hubbard U = 5.0 eV and Hund J0 = 1.0 eV to Mn-3d states,
and Hubbard U = 6.0 eV and Hund J0 = 1.2 eV to Ni-3d states. In the past, J0 was specifed
using the parameter Hubbard J0 in the system namelist. Note that J0 currently can be used
only for one Hubbard channel.

The code reads all lines in the HUBBARD card until the end of file is reached or until the next
card is found in the input.

Finally, note that currently the Dudarev’s DFT+U is not implemented for the noncollinear
spin-polarized case. However, Liechtenstein’s DFT+U supports the noncollinear spin-polarized
case, and so if you use this case then the code will automatically switch to the Liechtenstein’s
DFT+U .

3.2    DFT+U +J (Liechtenstein’s formulation)
Important notice: The Hubbard U and Hund J values shown in the examples below are
random values chosen just for the sake of demonstration purposes and they must not be used
for production calculations.

In the past, to use this case the user had to specify in the pw.x input file e.g. the following:

   &system
      ...
      lda_plus_u = .true.
      lda_plus_u_kind = 1
      U_projection_type = ’ortho-atomic’
      Hubbard_U(1)   = 5.0
      Hubbard_J(1,1) = 1.0
      Hubbard_J(2,1) = 1.1
      Hubbard_U(2)   = 6.0
      Hubbard_J(1,2) = 1.2
      Hubbard_J(2,2) = 1.3
   /

                                                9
```
