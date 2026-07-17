# INPUT_pw2bgw — NAMELIST: &INPUT_PW2BGW — Variable: vxc_integral

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2bgw.txt
- Retrieved: 2026-07-17T11:49:58+00:00
- Official source SHA-256: `5f52150cf5d567429fbca7663ea1ecd3841683947b6ecfd410873e0a6d134e55`
- Extracted text SHA-256: `1e2ea7f879213a0e9485a325b107e8bb1a86fdf6d39f63204ba565f32c45be23`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       vxc_integral
   
   Type:           STRING
   Default:        'g'
   Description:    'g' | 'r'
                   'g' to compute matrix elements of exchange-correlation potential in G-space.
                   'r' to compute matrix elements of the local part of exchange-correlation
                   potential in R-space. It is recommended to use 'g'. Not used if "vxc_flag" = .FALSE.
   +--------------------------------------------------------------------
   
```
