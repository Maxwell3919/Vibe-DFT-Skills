# INPUT_LD1 — NAMELIST: &TEST — Variable: file_pseudo

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `372e77cf748fa517a9a1be76a82003631b3389561e380dd20cc1ee73f998c1e9`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       file_pseudo
   
   Type:           CHARACTER
   Status:         ignored if "iswitch"=3
   Description:    File containing the PP.
                   
                   * If the file name contains  ".upf" or ".UPF",
                   the file is assumed to be in UPF format;
                   
                   * else if the file name contains ".rrkj3" or ".RRKJ3",
                   the old RRKJ format is first tried;
                   
                   * otherwise, the old NC format is read.
                   
                   IMPORTANT: in the latter case, all calculations are done
                   using the SEMILOCAL form, not the separable nonlocal form.
                   Use the UPF format if you want to test the separable form!
   Default:        ' '
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      ecutmin, ecutmax, decut
   
   Type:           REAL
   Default:        decut=5.0 Ry; ecutmin=ecutmax=0Ry
   Status:         specify "ecutmin" and "ecutmax" if you want to perform this test
   Description:    Parameters (Ry) used for test with a basis set of spherical
                   Bessel functions j_l(qr) . The hamiltonian at fixed scf
                   potential is diagonalized for various values of ecut:
                   "ecutmin", "ecutmin"+"decut", "ecutmin"+2*"decut" ... up to "ecutmax".
                   This yields an indication of convergence with the
                   corresponding plane-wave cutoff in solids, and shows
                   in an unambiguous way if there are "ghost" states
   +--------------------------------------------------------------------
   
```
