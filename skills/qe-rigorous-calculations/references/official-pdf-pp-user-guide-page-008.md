# pp_user_guide.pdf — page 8

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pp_user_guide.pdf
- Retrieved: 2026-07-17T11:53:40+00:00
- Official source SHA-256: `8f53208b6cafea0d02640a33d25839f15ff9c8478702b435582b19f31f6b79fb`
- Extracted text SHA-256: `6401ad420f6ef90b189f653ba5775472bd991804711d7cef856d06b9036decfd`
- Official Last-Modified: Mon, 08 Dec 2025 21:41:31 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
5    Troubleshooting
Almost all problems in Quantum ESPRESSO arise from incorrect input data and result in
error stops. Error messages should be self-explanatory, but unfortunately this is not always
true. If the code issues a warning messages and continues, pay attention to it but do not assume
that something is necessarily wrong in your calculation: most warning messages signal harmless
problems.

Some postprocessing codes complain that they do not find some files Most likely
you are not reading the correct data files, or you are not following the correct procedure for
postprocessing.
    For Linux PC clusters in parallel execution: in at least some versions of MPICH, the current
directory is set to the directory where the executable code resides, instead of being set to the
directory where the code is executed. This MPICH weirdness may cause unexpected failures
in some postprocessing codes that expect a data file in the current directory. Workaround: use
symbolic links, or copy the executable to the current directory.




                                               8
```
