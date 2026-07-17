# INPUT_POSTAHC — NAMELIST: &INPUT — Variable: skip_upper

- Official source: https://www.quantum-espresso.org/Doc/INPUT_POSTAHC.txt
- Retrieved: 2026-07-17T11:49:38+00:00
- Official source SHA-256: `b0aad4211a1be89d64be4c7694d543db458ec59846a3691661e37d08bd430636`
- Extracted text SHA-256: `e33446fc6464dff069ebe4ebfb6f1eaf1bb1f52ba4b618bdc08eeacd30f993c2`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:39 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       skip_upper
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true., skip calculation of the upper Fan self-energy. Also, truncate the
                   Debye-Waller self-energy to include only the low-energy band contribution.
                   (Corresponds to the second term (lower Fan + lower DW) of Eq. (G1-revised) of
                   J.-M. Lihm and C.-H. Park, PRX 12, 039901(E) (2022).)
                   If .false., calculate the contribution of both the high-energy and low-energy
                   bands. In this case, ahc_upfan_iq#.bin files must be present in "ahc_dir".
   +--------------------------------------------------------------------
   
```
