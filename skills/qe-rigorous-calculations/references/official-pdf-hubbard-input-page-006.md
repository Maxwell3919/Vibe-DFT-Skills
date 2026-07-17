# Hubbard_input.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `b30a53e263d135e861d547bf4595fbf2c4eda0674d6f200ecb82de4353a7302f`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 /
 &electrons
    conv_thr = 1.d-10
    mixing_beta = 0.7
 /
ATOMIC_SPECIES
 Mn 54.938 Mn.pbesol-spn-rrkjus_psl.0.3.1.UPF
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
U Mn-3p 3.0
U Ni-3d 6.0
U Ni-4s 2.0
In this example we apply U = 5.0 eV to Mn-3d states and U = 3.0 eV to Mn-3p states, where
3d appears first in the list and hence this is the first Hubbard channel/manifold for Mn while
3p appears second and hence this is the second Hubbard channel/manifold for Mn. Similarly,
we apply U = 6.0 eV to Ni-3d states and U = 2.0 eV to Ni-4s states. It is important to remark
that when the user specifies the Hubbard manifolds he/she must make sure that these states
are present in the pseudopotentials that are used.
    Moreover, it is possible to specify even 3 Hubbard channels/manifolds per atomic type.
However, in this case the 2nd and the 3rd Hubbard manifolds will be considered as one effective
manifold, and the same Hubbard U will be applied to this effective manifold. Please see the
example below:
&control
    calculation=’scf’
    restart_mode=’from_scratch’,
    prefix=’Ni2MnGa’
    pseudo_dir = ’../pseudo’
    outdir=’./tmp’
 /
 &system
    ibrav = 7, celldm(1) = 7.80, celldm(3) = 1.4142136,
    nat = 4, ntyp = 3, ecutwfc = 50.0, ecutrho = 400.0, nspin = 2,
    occupations =’smearing’, smearing =’mv’, degauss = 0.01,
    starting_magnetization(1) = 0.5,
    starting_magnetization(2) = 0.5
 /
 &electrons

                                              6
```
