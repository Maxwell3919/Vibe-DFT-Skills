# user_guide.pdf — page 25

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `8f812b7a0b0e5c58ef5928ae836700214f8595c88ae63ed6fa238366cc7431de`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2.9.6   Cray machines
Cray machines may be tricky: ”... despite what people can imagine, every CRAY machine
deployed can have different environment. For example on the machine I usually use for tests
[...] I do have to unload some modules to make QE running properly. On another CRAY [...]
there is also Intel compiler as option and the system is slightly different compared to the other.”
(info by Filippo Spiga)
     ./configure ARCH=craype should work for recent Cray machines. This selects the ftn
compiler, that typically uses the crayftn compiler but may also use other ones, depending
upon the site and personal environment. ftn v.15.0.1 and later should compile QE properly.
Some compiler versions may however run into problems like these for ftn v.14.0.3:

   • internal compiler error in esm_stres_mod.f90;

   • crashes when writing the final xml data file.

Workaround: compile codes esm_stres_mod.f90, Modules/qexsd*.f90, PW/src/pw_restart_new.f90
with reduced optimization, using -O0 or -O1 instead of the default -O3,fp3 optimization.
   If you want to use the Intel compiler instead, try something like:

$ module swap PrgEnv-cray PrgEnv-intel
$ ./configure ARCH=craype [--enable-openmp --enable-parallel --with-scalapack]




                                                25
```
