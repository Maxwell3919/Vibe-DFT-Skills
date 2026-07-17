# Hubbard_input.pdf — page 13

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `f11f5c329d74fa82fb9b5a6bef34c1c823242b9219fd76dca3c56348d095529f`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
V Co-3d O-2p 1 46 0.75
V Co-3d O-2p 1 43 0.75
V Co-3d O-2p 1 54 0.75
V Co-3d O-2p 1 11 0.75
V Co-3d O-2p 1 22 0.75
In this case, the code will detect U and V parameters in the HUBBARD card, and so the code
will consider this as being a DFT+U +V calculation. The first line in the HUBBARD card corre-
sponds to the on-site Hubbard U parameter that is used for Co-3d states, and the value of this
parameter is 7.70 eV. Note that the equivalent allowed syntax for this first line is the following:
V Co-3d Co-3d 1 1 7.70
All the other lines in the HUBBARD card above correspond to the inter-site Hubbard V param-
eters between Co-3d and O-2p states. Why do we have 6 of them? Because in LiCoO2 each
Co atom has 6 nearest neighbors (octahedral coordination geometry for Co atoms). In this
example, all 6 O atoms are at the same distance from Co, so the value of V parameters are all
equal to 0.75 eV. but in general, there might be complex distortion of the structure, and hence
there might be different Co-O distances and hence the values of V parameters will be somewhat
different. The indices that appear in the 4th and 5th columns of the V entries correspond to
the na and nb indices of the arrays Hubbard V(na,nb,k) that are still used internally in the
pw.x code. If we have just one occurrence of V for a given couple of indices na and nb, then this
will be attributed to k=1, i.e. the so-called “standard-standard” interaction. In this example,
the “standard-standard” interaction means that we take into account the interaction between
Co-3d and O-2p states.

Below we give a more advanced example that shows how to take into account also other types
of inter-site interactions.
&control
    calculation=’scf’
    restart_mode=’from_scratch’,
    prefix=’LiCoO2’
    pseudo_dir = ’../pseudo’
    outdir=’./tmp’
 /
 &system
    ibrav = 5, celldm(1) = 9.3705, celldm(4) = 0.83874,
    nat = 4, ntyp = 3, ecutwfc = 50.0, ecutrho = 400.0
 /
 &electrons
    conv_thr = 1.d-10
    mixing_beta = 0.7
 /
ATOMIC_SPECIES
 Co 59.0    Co.pbesol-spn-rrkjus_psl.0.3.1.UPF
 O   16.0   O.pbesol-n-rrkjus_psl.0.1.UPF
 Li   7.0   Li.pbesol-s-rrkjus_psl.0.2.1.UPF
ATOMIC_POSITIONS (crystal)

                                                13
```
