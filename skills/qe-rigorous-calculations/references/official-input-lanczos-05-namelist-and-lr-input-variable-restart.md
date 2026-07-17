# INPUT_Lanczos — NAMELIST: &LR_INPUT — Variable: restart

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Lanczos.txt
- Retrieved: 2026-07-17T11:49:18+00:00
- Official source SHA-256: `58c02f4cb1fdefbef4203bbe55d16af2a768acd7cfb5462fc62bd1dfd07cb530`
- Extracted text SHA-256: `dc82c0b42d72a84b4fa30d22d11295f53f9a1ad4f159ae28950f6c34eaa52ccc`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       restart
   
   Type:           LOGICAL
   Default:        .false.
   Description:    When set to .true., turbo_lanczos.x will attempt to restart
                   from a previous interrupted calculation. (see "restart_step"
                   variable).
                   
                   Beware, if set to .false. turbo_lanczos.x will OVERWRITE any
                   previous runs.
   +--------------------------------------------------------------------
   
```
