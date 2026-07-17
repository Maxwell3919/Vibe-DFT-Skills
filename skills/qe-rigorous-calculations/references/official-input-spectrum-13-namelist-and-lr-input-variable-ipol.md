# INPUT_Spectrum — NAMELIST: &LR_INPUT — Variable: ipol

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Spectrum.txt
- Retrieved: 2026-07-17T11:49:51+00:00
- Official source SHA-256: `aa5de63566220ec9338215bdedcd16fa6ed031b02a440ef56150326a2aacb424`
- Extracted text SHA-256: `7a4d2fab10391053c2555397abb6802e02b4161178bb43e4ab33b21dad877791`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ipol
   
   Type:           INTEGER
   Default:        1
   Description:    An integer variable that determines which element of the
                   dynamical polarizability will be computed:
                   1 -> alpha_xx(omega), 2 -> alpha_yy(omega), and
                   3 -> alpha_zz(omega). When set to 4, three Lanczos chains
                   are sequentially performed and the full polarizability
                   tensor and the absorption coefficient are computed.
   +--------------------------------------------------------------------
   
```
