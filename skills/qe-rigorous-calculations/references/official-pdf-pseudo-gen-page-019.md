# pseudo-gen.pdf — page 19

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `f719fe9d9d5abbfa7c91b248452cf3f6065baa0b044f86fb7dd8edbc5d05cea9`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
       20                                                                          1
                                                         ’ld10.dlog’ u 1:2                                  ’ld10ps.wfc’ u 1:2
                                                         ’ld10.dlog’ u 1:3                                  ’ld10ps.wfc’ u 1:3
                                                         ’ld10.dlog’ u 1:4                                  ’ld10ps.wfc’ u 1:4
                                                      ’ld10ps.dlog’ u 1:2                                   ’ld10ps.wfc’ u 1:5
                                                      ’ld10ps.dlog’ u 1:3                                   ’ld10ps.wfc’ u 1:6
       15                                             ’ld10ps.dlog’ u 1:4        0.8                        ’ld10ps.wfc’ u 1:7




       10                                                                        0.6




        5                                                                        0.4




        0                                                                        0.2




        -5                                                                         0




       -10                                                                       -0.2




       -15                                                                       -0.4




       -20                                                                       -0.6
             -4   -3.5   -3   -2.5   -2   -1.5   -1         -0.5             0          0   1   2   3   4                        5




    Both the orbitals and the logarithmic derivatives (note the different energy range)
start to exhibit some visible discrepancy now.
    One can try to fiddle with all generation parameters, better if one at the time, to
see whether things improve. Curiously enough, the pseudization radius for the core
correction, which in principle should be as small as possible, seems to improve things
if pushed slightly outwards (try rcore=2.0). Also surprisingly, a smaller pseudization
radius for the 3d state, 0.9 or 1.0 a.u., doesn’t bring any visible improvement to trans-
ferability (but it increases a lot the required cutoff!). Changing the pseudization radii
for 4s and 4p states doesn’t affect much the results.
    A different local potential – a pseudized version of the total self-consistent potential
– can be chosen by setting lloc=-1 and setting rcloc to the desired pseudization radius
(a.u.). For small rcloc ghosts re-appear; rcloc=2.9 yields slighty better total energy
differences but slightly worse eigenvalues. Note that the PP so generated will also have
a s projector, while the previous ones had only p and d projectors.
    One could also generate the PP from a different electronic configuration. Since Ti
tends to lose rather than to attract electrons, it will be more easily found in a ionized
state than in the neutral one. One might for instance use the electronic configuration
of the Bachelet-Hamann-Schlüter paper[4]: 3d2 4s0.75 4p0.25 . This however doesn’t seem
to improve much.
    Finally we end up with these generation data:

 &input
   atom=’Ti’, dft=’PBE’, config=’[Ar] 3d2 4s2 4p0’,
   iswitch=3
 /
 &inputp
   pseudotype=1, nlcc=.true., rcore=2.0, lloc=0,
   file_pseudopw=’Ti.pbe-n-rrkj.UPF’
 /
3
4P 2 1 0.00 0.00 2.9 2.9
3D 3 2 2.00 0.00 1.3 1.3
4S 1 0 2.00 0.00 2.9 2.9
```
