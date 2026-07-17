# INPUT_PW — NAMELIST: &IONS — Variable: upscale

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `52872e930ecf42b4d76c93f612f47d6038bc6e082744576908298961e0cfccb9`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       upscale
      
      Type:           REAL
      Default:        100.D0
      Description:    Max reduction factor for "conv_thr" during structural optimization
                      "conv_thr" is automatically reduced when the relaxation
                      approaches convergence so that forces are still accurate,
                      but "conv_thr" will not be reduced to less that "conv_thr" / "upscale".
      +--------------------------------------------------------------------
      
```
