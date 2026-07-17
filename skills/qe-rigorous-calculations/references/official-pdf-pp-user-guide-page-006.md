# pp_user_guide.pdf — page 6

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pp_user_guide.pdf
- Retrieved: 2026-07-17T11:53:40+00:00
- Official source SHA-256: `8f53208b6cafea0d02640a33d25839f15ff9c8478702b435582b19f31f6b79fb`
- Extracted text SHA-256: `ddd19a10694a41f131f4fcc874d0a83529ddbee105f78e825d7270710f1c8e37`
- Official Last-Modified: Mon, 08 Dec 2025 21:41:31 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
  1. Run pw.xwith K_POINT automatic.

  2. Run

      $ fermi_velocity.x -in {pw.x input file}

  3. vfermi.frmsf is generated

   fermi_proj.x generates a color plot of an orbital character. You use it as follows:

  1. Run pw.xwith K_POINT automatic.

  2. Run projwfc.x just to generate {prefix}.save/atomic_proj.*.

  3. Run

      $ fermi_proj.x -in {input file}

      Input-file format is as follows:

      &PROJWFC
       {The same as the input of projwfc.x}
      /
      {Number of target wavefunctions}
      {Index of target WFC1} {Index of target WFC2} {Index of target WFC3} ...
                   Pntarget
      It generates i=1      |⟨φatom             2
                               target(i) |φnk ⟩| , where ns and target(i) are the number of the target
      wavefunctions and the indices of target wavefunctions, respectively.

  4. The above quantity is written into "proj.frmsf", which can be read by FermiSurfer
     program.

   There is an example of fermi_velocity.x and fermi_proj.x in fermisurf_example/.

4.6    Wannier functions
There are several Wannier-related utilities in PostProc:

  1. The ”Poor Man Wannier” code pmw.x, to be used in conjunction with DFT+U calcula-
     tions: see Example 05.

  2. The interface with Wannier90 code, pw2wannier.x: see the documentation in W90/
     (you may install the Wannier90 plug-in via make w90 ). For spin-current matrix el-
     ements, implemented in routine compute shc: “it writes .sIu and .sHu files used for
     WANNIER-BERRI (https://github.com/stepan-tsirkin/wannier-berri/), and also will be
     utilized through postw90.x (https://github.com/manxkim/wannier90/tree/SHC/src) in
     Wannier90. In WANNIER-BERRI, .sHu and .sIu files can be used to calculate the quan-
     tity ”opt SHCryoo”. In Wannier90, add ”berry task = shc” and ”shc ryoo=.true.”. in
     the input parameters of postw90.x. They activate the calculation of SHC using .sHu and
     .sIu.”

                                                  6
```
