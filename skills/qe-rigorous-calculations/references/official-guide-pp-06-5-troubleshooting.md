# 5 Troubleshooting

- Official source: https://www.quantum-espresso.org/Doc/pp_user_guide/node14.html
- Retrieved: 2026-07-17T11:52:14+00:00
- Official source SHA-256: `3942504f2ffa65a79a920084b461c64877d27334b9cc4d9a9894b4b8850fe5cc`
- Extracted text SHA-256: `babfdd962fad00474e6eccf2f2b7a068a5760782ec9c22d6b37ca1ccdf623383`
- Official Last-Modified: Mon, 08 Dec 2025 21:39:56 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

About this document ...

Up:

User's Guide for the PP

Previous:

4.8 Other tools

  

Contents

5 Troubleshooting

Almost all problems in Q
UANTUM 
ESPRESSO arise from incorrect input data and result in
error stops. Error messages should be self-explanatory, but unfortunately
this is not always true. If the code issues a warning messages and continues,
pay attention to it but do not assume that something is necessarily wrong in
your calculation: most warning messages signal harmless problems.

5.0.0.1 Some postprocessing codes complain that they do not find some files

Most likely you are not reading the correct data files, or you are not
following the correct procedure for postprocessing.

For Linux PC clusters in parallel execution: in at least some versions
of MPICH, the current directory is set to the directory where the executable
code resides, instead of being set to the directory where the code is executed.
This MPICH weirdness may cause unexpected failures in some postprocessing
codes that expect a data file in the current directory. Workaround: use
symbolic links, or copy the executable to the current directory.

Subsections

5.0.0.1 Some postprocessing codes complain that they do not find some files
```
