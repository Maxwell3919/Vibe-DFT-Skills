# INPUT_PH — NAMELIST: &INPUTPH — Item: do_long_range

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PH.html
- Retrieved: 2026-07-17T11:49:34+00:00
- Official source SHA-256: `2390c593c99833da82b470e7b72d2b39c20ae6b6613e904e270e2ae9d673d4fc`
- Extracted text SHA-256: `dbbbe482c5f818dd69dcb1758d11d0ee565daf1056b1023dc1d52a19974940f2`
- Official Last-Modified: Fri, 16 Jan 2026 09:36:37 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


do_long_range

LOGICAL

Default:

.false.

If .true., add the long-range part of the potential
to the Fourier interpolated potential as in:
S. Ponce et al, J. Chem. Phys. 143, 102813 (2015).
Reads dielectric matrix and Born effective charges from
the ${wpot_dir}/tensors.dat file, written in dvscf_q2r.x.
Currently, only the dipole (Frohlich) part is implemented.
The quadrupole part is not implemented.

[
Back to Top
]
```
