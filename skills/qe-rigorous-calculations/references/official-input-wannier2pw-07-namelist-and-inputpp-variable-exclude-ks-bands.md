# INPUT_wannier2pw — NAMELIST: &INPUTPP — Variable: exclude_ks_bands

- Official source: https://www.quantum-espresso.org/Doc/INPUT_wannier2pw.txt
- Retrieved: 2026-07-17T11:50:03+00:00
- Official source SHA-256: `5ebe5d8a42dbaf47d03e86a148f958584243bd68b976f32492185b6884563012`
- Extracted text SHA-256: `f9ceda89f87a284fda7e568271fd473bc9ed33dd2948a90620214723472c1b7a`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exclude_ks_bands
   
   Type:           INTEGER
   Description:    This variable is used only when hubbard = .true. This variable specifies
                   how many lowest-lying Kohn-Sham bands must be excluded from the summation
                   when building the Wannier functions using Umn matrices from Wannier90
                   (those bands which are below the energy where the wannierization starts)
   Default:        0
   +--------------------------------------------------------------------
   
```
