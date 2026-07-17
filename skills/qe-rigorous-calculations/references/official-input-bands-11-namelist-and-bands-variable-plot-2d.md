# INPUT_BANDS — NAMELIST: &BANDS — Variable: plot_2d

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BANDS.txt
- Retrieved: 2026-07-17T11:48:54+00:00
- Official source SHA-256: `b8b1193c4f2723310151d7825240f9b20fe2212d1e0f509cce89988a93f7a14a`
- Extracted text SHA-256: `7eae3890166e44af4c86e0f935a935816688e3a7a052df103ed5a1c956593875`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       plot_2d
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true. writes the eigenvalues in the output file
                   in a 2D format readable by gnuplot. Band ordering is not
                   changed. Each band is written in a different file called
                   filband.# with the format:
                   
                      xk, yk, energy
                      xk, yk, energy
                      ..  ..  ..
                   
                   energies are written in eV and xk in units 2\pi/a.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      firstk, lastk
   
   Type:           INTEGER
   Description:    if "lsym"=.true. makes the symmetry analysis only for k
                   points between firstk to lastk
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:28:58 CEST 2025
```
