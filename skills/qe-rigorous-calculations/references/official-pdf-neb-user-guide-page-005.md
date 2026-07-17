# neb_user_guide.pdf — page 5

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/neb_user_guide.pdf
- Retrieved: 2026-07-17T11:53:27+00:00
- Official source SHA-256: `acc9df963f4b8009b54b8f253bf207386ed0fd2793881764886022af09c58d2a`
- Extracted text SHA-256: `484b69815828b146bdb3e798fe5d16d97e7291773409e5eaac4b4646ade8d6e6`
- Official Last-Modified: Mon, 08 Dec 2025 21:37:56 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
prefix.int contains an interpolation of the path energy profile that pass exactly through each
     image; it is computed using both the image energies and their derivatives
prefix.path information used by Quantum ESPRESSO to restart a path calculation, its
     format depends on the input details and is undocumented
prefix.axsf atomic positions of all path images in the XCrySDen animation format: to visu-
     alize it, use xcrysden --axsf prefix.axsf
prefix.xyz atomic positions of all path images in the generic xyz format, used by many
     quantum-chemistry softwares
prefix.crd path information in the input format used by pw.x, suitable for a manual restart
     of the calculation
where prefix is the PWscf variable specified in the input. The more verbose output from the
PWscf engine is not printed on the standard output, but is redirected into a file stored in the
image-specific temporary directories (e.g. outdir/prefix 1/PW.out for the first image, etc.).
   NEB calculations are a bit tricky in general and require extreme care to be setup correctly.
Sometimes it can easily take hundreds of iterations for them to converge, depending on the
number of atoms and of images. Here you can find some advice (courtesy of Lorenzo Paulatto):
  1. Don’t use Climbing Image (CI) from the beginning. It makes convergence slower, espe-
     cially if the special image changes during the convergence process (this may happen if
     CI scheme=’auto’ and if it does it may mess up everything). Converge your calcula-
     tion, then restart from the last configuration with CI option enabled (note that this will
     increase the barrier).
  2. Carefully choose the initial path. If you ask the code to use more images than those you
     have supplied on input, the code will make a linear interpolation of the atomic positions
     between consecutive input images. You can visualize the .axsf file with XCrySDen as
     an animation: take some time to check if any atoms overlap or get very close in some of
     the new images (in that case you will have to supply intermediate images). Remember
     that Quantum ESPRESSO assumes continuity between two consecutive input images
     to initialize the path. In other words, periodic images are not used by default, so that
     an unwanted path could result if some atom crosses the border of the unit cell and it is
     refolded in the unit cell in the input image. The problem can be solved by activating the
     mininum image option, which choses an appropriate periodic replica of any atom that
     moves by more than half the size of the unit cell between two consecutive input images.
     If this does not work either, you may have to manually translate an atom by one or more
     unit cell base vectors in order to have a meaningful initial path.
  3. Try to start the NEB process with most atomic positions fixed, in order to converge the
     more ”problematic” ones, before leaving all atoms move.
  4. Especially for larger systems, you can start NEB with lower accuracy (less k-points, lower
     cutoff) and then increase it when it has converged to refine your calculation.
  5. Use the Broyden algorithm instead of the default one: it is a bit more fragile, but it
     removes the problem of ”oscillations” in the calculated activation energies. If these oscil-
     lations persist, and you cannot afford more images, focus to a smaller problem, decompose
     it into pieces.

                                               5
```
