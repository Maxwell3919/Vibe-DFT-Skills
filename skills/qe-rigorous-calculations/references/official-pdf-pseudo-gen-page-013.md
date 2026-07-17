# pseudo-gen.pdf — page 13

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `0131e89f066e9230ac7ab3afeaa40a4294a216b2a3610c5fdf066e931c8a6a42`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
will be written in UPF format to file Ti.pbe-n-rrkj.UPF (following the quantum
ESPRESSO convention for PP names). Following the two namelists, there is a list of
states used for pseudization: the 4S state, with pseudization radius rc = 2.9 a.u.; the
3D state, rc = 1.3 a.u.; the 4P, rc = 2.9 a.u., listed as last because it is the channel to
be chosen as local potential.
    There is nothing magic or especially deep in the choice of the radius and energy
range for logarithmic derivatives, of the local potential and of pseudization radii: it is
just a reasonable guess. Running the input, one gets an error:

       Wfc   4S rcut= 2.883 Estimated cut-off energy=                      14.82 Ry
      l=   0 Node at 0.71997236
       This function has    1 nodes for 0 < r <  2.883

 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
     from compute_phi : error #         1
     phi has nodes before r_c
 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

This means that the 4S pseudized orbitals has one node. With RRKJ pseudization
(the default), this may occasionally happen. One can either choose TM pseudization
(tm=.true.) or set a small value of ρ(r = 0) (e.g. rho0=0.001). Let us do the
latter. You should carefully look at the output, which will consists in an all-electron
calculation, followed by the pseudopotential generation step, followed by a final test.
In particular, notice this message about the nonlinear core correction:

       Computing core charge for nlcc:

        r > 1.73 : true rho core
        r < 1.73 : rho core = a sin(br)/r                a=   2.40    b=      1.56

       Integrated core pseudo-charge :            3.43

(this is actually not an ideal situation: the pseudization radius for the charge density
                                                                          (min)    (l=2)
should be smaller than all pseudization radii; in our case, smaller than rc     = rc     =
1.3 a.u.). Also notice messages on pseudization:

       Wfc   4S rcut= 2.883 Estimated cut-off energy=                           5.32 Ry
       Using 4 Bessel functions for this wfc, rho(0) = 0.001
       This function has    0 nodes for 0 < r <    2.883

       Wfc   3D rcut= 1.296 Estimated cut-off energy=                         137.82 Ry
       This function has   0 nodes for 0 < r <   1.296

(note the large difference between the estimated cutoff for the s and the d channel! Of
course, it is only the latter the “problem” one here); and look at the final consistency
check:

      n l       nl                 e AE (Ry)             e PS (Ry)         De AE-PS (Ry)
```
