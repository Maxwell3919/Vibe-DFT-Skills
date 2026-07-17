# pp_user_guide.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pp_user_guide.pdf
- Retrieved: 2026-07-17T11:53:40+00:00
- Official source SHA-256: `8f53208b6cafea0d02640a33d25839f15ff9c8478702b435582b19f31f6b79fb`
- Extracted text SHA-256: `788dc5b537bbd0068dbe1eb5581d9c207af9623008664e45835819ea1db1a5f1`
- Official Last-Modified: Mon, 08 Dec 2025 21:41:31 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
4.3       Band structure, Fermi surface
The code bands.x reads data file(s), extracts eigenvalues, regroups them into bands (the algo-
rithm used to order bands and to resolve crossings may not work in all circumstances, though).
The output is written to a file in a simple format that can be directly read and converted to
plottable format by auxiliary code plotband.x. Unpredictable plots may results if k-points
are not in sequence along lines, or if two consecutive points are the same. The code bands.x
performs as well a symmetry analysis of the band structure. For a complete input description,
see Doc/INPUT bands.*. See Example 01, Example 04 and Example 06 for simple band plots.
    The plotting of Fermi surfaces can be performed using code fs.x. The resulting file in .bxsf
format can be read and plotted using XCrySDen. See Example 02 for an example of Fermi
surface visualization (Ni, including the spin-polarized case).

4.4       Projection over atomic states, DOS, projected band structure
The code projwfc.x calculates projections of wavefunctions over atomic orbitals. The atomic
wavefunctions are those contained in the pseudopotential file(s). The Löwdin population anal-
ysis (similar to Mulliken analysis) is presently implemented. The projected DOS (or PDOS:
the DOS projected onto atomic orbitals) can also be calculated and written to file(s). More de-
tails on the input data are found in file PP/Doc/INPUT PROJWFC.*. The ordering of the various
angular momentum components (defined in routine ylmr2.f90) is as follows: P0,0 (t), P1,0 (t),
P1,1 (t)cosϕ, P1,1 (t)sinϕ, P2,0 (t), P2,1 (t)cosϕ, P2,1 (t)sinϕ, P2,2 (t)cos2ϕ, P2,2 (t)sin2ϕ and so on,
where Pl,m =Legendre Polynomials, t = cosθ = z/r, ϕ = atan(y/x).
    Data produced by code projwfc.x can be further analysed using auxiliary codes sumpdos.x
(sums selected PDOS by specifying the names of files containing the desired PDOS: type
sumpdos.x -h or look into the source code for more details) and plotproj.x . A more so-
phisticated tools is the script PP/tools/sum states.py, by Julen Larrucea: documentation in
http://larrucea.eu/sum states-py-2/.
    The total electronic DOS can also be calculated by code dos.x, whose complete input
documentation is in PP/Doc/INPUT DOS.* See Example 02 for total and projected electronic
DOS calculations, -and for projected band structure; see Example 03 for projected and local
DOS calculations.
    The DOS projected over molecular states (e.g. for a molecule on a surface system) can be
computed using code molecularpdos.x (courtesy of Guido Fratesi). See file PP/Doc/INPUT MOLDOS.*
for input documentation and directory PP/examples/MolDos example/ for an example.
    The calculation of magnetic anisotropy using the Force Theorem is described in the following
paper: https://journals.aps.org/prb/abstract/10.1103/PhysRevB.90.205409. An example and
a README can be found in PP/examples/ForceTheorem example/

4.5       Color plot of the Fermi velocity and the orbital character on
          Fermi surfaces
You can plot any quantity on Fermi surfaces as a color plot by using fermisurfer program1 .
fermi_velocity.x and fermi_proj.x are used to generate an input file for fermisurfer from
the output of pw.xor projwfc.x.
   fermi_velocity.x generates a color-plot of Fermi velocity. You use it as follows:
  1
      http://osdn.jp/projects/fermisurfer/


                                                5
```
