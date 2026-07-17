# Hubbard_input.pdf — page 4

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `a605ff93cd4ffc3d9f77535e871d42f1a460f6857dfc6ec501aed0f070258946`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 Mn 0.0000000000   0.0000000000           0.0000000000
 Ni 0.5000000000   0.7500000000           0.2500000000
 Ni 0.5000000000   0.2500000000           0.7500000000
 Ga 0.0000000000   0.5000000000           0.5000000000
K_POINTS (automatic)
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
U Mn-3d 5.0
U Ni-3d 6.0
Note that in the example above we do not specify any parameters related to DFT+U in the
system namelist (contrary to what was done in the past). All Hubbard-related parameters are
now specified in the new card called “HUBBARD”. The user has to specify the type of the
Hubbard projectors that will be used in DFT+U . This is done by writing the type of projectors
on the same line where the HUBBARD card name appears. In the past the type of Hubbard
projectors was specified using the input keyword U projection type, which is no longer used.
And now it is not needed to specify lda plus u=.true.
    The possible options for Hubbard projectors are: atomic, ortho-atomic, norm-atomic, wf,
and pseudo. There is no default for Hubbard projectors, i.e. the user must specify it. Please
see /Doc/INPUT PW.txt for the description of these options. The most frequently used types
of projectors are atomic and ortho-atomic. It is recommended use ortho-atomic whenever
possible. The advantage of ortho-atomic over atomic is that the Hubbard corrections are
applied only once in the former case, while in the latter case they are applied twice in the
orbital overlap regions. So generally ortho-atomic Hubbard projectors give more accurate
results (e.g. atomic occupations) that those obtained using the atomic Hubbard projectors. If
you are interested to learn more about the Hubbard projectors you are invited to check e.g.
Refs. [13, 14].
    In the example above, we specified the Hubbard U values of 5.0 and 6.0 eV for Mn-3d and
Ni-3d states, respectively. Here, 3d are the Hubbard manifolds. Previously these manifolds were
tabulated and hard-coded in the routines Modules/set hubbard l.f90. Now these manifolds
must be specified in the HUBBARD card for each chemical element. The initial occupations of
these manifolds were previously tabulated and hard-coded in PW/src/tabd.f90, but now the
initial occupations are read from the pseudopotentials. If the user is not happy with this default
behavior of the code, then it is possible to overwrite these initial occupations by specifying them
in the input file in the system namelist using a new keyword Hubbard occ(ityp,i), where ityp
is the atomic type number (see ATOMIC SPECIES), and i runs from 1 to 3 (because there can
be up to 3 Hubbard manifolds per one atomic type - see more below). The example is given
below:
&control
    calculation=’scf’
    restart_mode=’from_scratch’,
    prefix=’Ni2MnGa’
    pseudo_dir = ’../pseudo’
    outdir=’./tmp’
 /
 &system
    ibrav = 7, celldm(1) = 7.80, celldm(3) = 1.4142136,

                                                4
```
