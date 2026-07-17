# INPUT_EELS — NAMELIST: &LR_INPUT — Variable: restart

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `d2a07c29dac8717746a7f8ea0b9f1858cd298f992d150e91564046730e2c6f39`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       restart
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true., turbo_eels.x will attempt to restart
                   from a previous interrupted calculation. (see "restart_step"
                   variable).
                   Beware, if set to .false. turbo_eels.x will OVERWRITE any
                   previous runs.
   +--------------------------------------------------------------------
   
```
