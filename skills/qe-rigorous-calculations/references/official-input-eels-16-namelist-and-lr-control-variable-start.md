# INPUT_EELS — NAMELIST: &LR_CONTROL — Variable: start

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `682233fa03402022a1d99abd50646ccdbd72d8b224e7fa72b5b0fe593ac2de58`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       start
   
   Type:           REAL
   Default:        0.0
   See:            end, increment
   Description:    This variable is used only when "calculator" = 'sternheimer'.
                   "start" is the value of frequency starting from which the
                   susceptibility and the loss function (-Im(1/eps)) will be computed.
                   "start" is specified in units controlled by "units".
   +--------------------------------------------------------------------
   
```
